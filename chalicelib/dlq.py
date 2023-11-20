import json
from botocore.exceptions import ClientError
from chalicelib.events import EventLogger


class DeadLetterQueue:
    # Initialize DLQ with AWS SQS resource and an event logger for monitoring.
    def __init__(self, sqs_resource, event_logger: EventLogger):
        self.sqs = sqs_resource
        self.queue_name = "dlq"
        self.queue_url = None  # Queue URL will be determined dynamically.
        self.event_logger = event_logger

        self._create_queue_if_not_exists()  # Ensure queue exists during object initialization.

    # Checks for the existence of the queue and creates it if it does not exist.
    def _create_queue_if_not_exists(self):
        try:
            # List queues to avoid unnecessary creation calls.
            response = self.sqs.list_queues(
                QueueNamePrefix=self.queue_name, MaxResults=1
            )
            if len(response["QueueUrls"]) > 0:
                self.queue_url = response["QueueUrls"][0]
            else:
                self._create_queue()
        except ClientError as e:
            self.event_logger.error(
                event={"message": f"Couldn't find queue {self.queue_name}."}
            )

    # Encapsulates the queue creation logic.
    def _create_queue(self):
        try:
            # Creation is simple but can be extended by adding attributes if needed.
            response = self.sqs.create_queue(QueueName=self.queue_name, Attributes={})
            self.queue_url = response["QueueUrl"]
            # Log creation for audit purposes.
            self.event_logger.info(
                event={"message": f"Queue created: {self.queue_url}"}
            )
        except Exception as e:
            # Capture all exceptions to log any queue creation issues.
            self.event_logger.error(event={"message": f"Queue creation failed: {e}"})

    # Sends a message to the DLQ.
    def send(self, message, attributes=None):
        attributes = attributes or {}
        try:
            # Serialize message to JSON for SQS compatibility.
            self.sqs.send_message(
                QueueUrl=self.queue_url,
                MessageBody=json.dumps(message),
                MessageAttributes=attributes,
            )
            # Log every message sent for traceability.
            self.event_logger.info(
                event={"message": f"Sent message to DLQ {self.queue_name}: {message}"}
            )
        except Exception as e:
            # Log failures to send messages to ensure visibility into delivery issues.
            self.event_logger.error(
                event={
                    "message": f"Failed to send message to DLQ {self.queue_name}. Error: {e}"
                }
            )
