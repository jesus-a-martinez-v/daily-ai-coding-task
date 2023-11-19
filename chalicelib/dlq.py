import json

from botocore.exceptions import ClientError

from chalicelib.events import EventLogger


class DeadLetterQueue:
    def __init__(self, sqs_resource, event_logger: EventLogger):
        self.sqs = sqs_resource
        self.queue_name = "dlq"
        self.queue_url = None
        self.event_logger = event_logger

        self._create_queue_if_not_exists()

    def _create_queue_if_not_exists(self):
        try:
            response = self.sqs.list_queues(
                QueueNamePrefix=self.queue_name, MaxResults=1
            )
            if len(response["QueueUrls"]) > 0:
                self.queue_url = response["QueueUrls"][0]
            else:
                self._create_queue()
        except ClientError as e:
            self.event_logger.error(
                event={"message": f"Couldn't find queue {self.queue_name}. Creating..."}
            )

    def _create_queue(self):
        try:
            response = self.sqs.create_queue(QueueName=self.queue_name, Attributes={})
            self.queue_url = response["QueueUrl"]
            self.event_logger.info(
                event={
                    "message": f"Created queue with name {self.queue_name}. URL: {self.queue_url}"
                }
            )
        except Exception as e:
            self.event_logger.error(
                event={
                    "message": f"Couldn't create queue {self.queue_name}. Error: {e}"
                }
            )

    def send(self, message, attributes=None):
        if attributes is None:
            attributes = {}

        try:
            self.sqs.send_message(
                QueueUrl=self.queue_url,
                MessageBody=json.dumps(message),
                MessageAttributes=attributes,
            )
            self.event_logger.info(
                event={"message": f"Sent message to DLQ {self.queue_name}: {message}"}
            )
        except Exception as e:
            self.event_logger.error(
                event={
                    "message": f"Failed to send message to DLQ {self.queue_name}. Error: {e}"
                }
            )
