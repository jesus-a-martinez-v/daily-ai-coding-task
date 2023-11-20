import json

# Import configuration settings and utility functions from the local package.
from . import config
from . import utils


# Define a class to handle event logging with AWS CloudWatch.
class EventLogger:
    def __init__(self, client):
        try:
            # Initialize with an AWS client and create necessary log groups and streams.
            self.client = client
            self._create_log_group()
            self._create_log_streams()
        except Exception as e:
            # If initialization fails, print an error and re-raise the exception.
            print("[FATAL] Could not initialize EventLogger", e)
            raise

    def _create_log_group(self):
        # Check if the specified log group already exists in AWS CloudWatch.
        exists = False
        response = self.client.describe_log_groups(logGroupNamePrefix=config.LOG_GROUP)

        # If the log group is found, set `exists` to True.
        for each_line in response["logGroups"]:
            if config.LOG_GROUP == each_line["logGroupName"]:
                exists = True
                break

        # If it doesn't exist, create a new log group with the specified tags and retention policy.
        if not exists:
            self.client.create_log_group(
                logGroupName=config.LOG_GROUP,
                tags={
                    "Frequency": "30 seconds",
                    "Environment": "Development",
                    "RetentionPeriod": str(config.RETENTION_PERIOD_IN_DAYS),
                    "Type": "Backend",
                },
            )

            # Set the retention policy for the log group.
            self.client.put_retention_policy(
                logGroupName=config.LOG_GROUP,
                retentionInDays=config.RETENTION_PERIOD_IN_DAYS,
            )

    def _create_log_streams(self):
        # Define log streams to be created within the log group.
        log_streams = [
            config.STATUS_LOG_STREAM,
            config.INFO_LOG_STREAM,
            config.ERROR_LOG_STREAM,
        ]
        response = self.client.describe_log_streams(logGroupName=config.LOG_GROUP)
        existing_log_streams = [s["logStreamName"] for s in response["logStreams"]]

        # Create any log streams that do not already exist.
        for log_stream in log_streams:
            if log_stream not in existing_log_streams:
                self.client.create_log_stream(
                    logGroupName=config.LOG_GROUP, logStreamName=log_stream
                )

    # Define methods to log different types of events.
    def info(self, event):
        # Log an informational event.
        self._log_event(log_stream_name=config.INFO_LOG_STREAM, event=event)

    def error(self, event):
        # Log an error event.
        self._log_event(log_stream_name=config.ERROR_LOG_STREAM, event=event)

    def status(self, event):
        # Log a status event.
        self._log_event(log_stream_name=config.STATUS_LOG_STREAM, event=event)

    def peek_status(self):
        # Retrieve the latest status event.
        events = self._get_events(config.STATUS_LOG_STREAM, limit=1)

        # If there is a status event, return it as a JSON object.
        if len(events) > 0:
            return json.loads(events[0]["message"])

        return None

    def _log_event(self, log_stream_name, event):
        # Log a single event to the specified log stream.
        self._log_events(log_stream_name, events=[event])

    def _log_events(self, log_stream_name, events):
        # Add a timestamp to each event if it doesn't already have one, then log the events.
        for event in events:
            if "timestamp" not in event:
                event["timestamp"] = utils.get_timestamp_millis()

        # Send the log events to the specified log stream in AWS CloudWatch.
        self.client.put_log_events(
            logGroupName=config.LOG_GROUP,
            logStreamName=log_stream_name,
            logEvents=events,
        )

    def _get_events(self, log_stream_name, limit=100):
        # Retrieve a list of events from the specified log stream.
        response = self.client.get_log_events(
            logGroupName=config.LOG_GROUP,
            logStreamName=log_stream_name,
            limit=limit,
        )

        return response["events"]
