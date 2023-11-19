import json

from . import config
from . import utils


class EventLogger:
    def __init__(self, client):
        try:
            self.client = client
            self._create_log_group()
            self._create_log_streams()
        except Exception as e:
            print("[FATAL] Could not initialize EventLogger", e)
            raise

    def _create_log_group(self):
        exists = False

        response = self.client.describe_log_groups(logGroupNamePrefix=config.LOG_GROUP)

        for each_line in response["logGroups"]:
            if config.LOG_GROUP == each_line["logGroupName"]:
                exists = True
                break

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

            self.client.put_retention_policy(
                logGroupName=config.LOG_GROUP,
                retentionInDays=config.RETENTION_PERIOD_IN_DAYS,
            )

    def _create_log_streams(self):
        log_streams = [
            config.STATUS_LOG_STREAM,
            config.INFO_LOG_STREAM,
            config.ERROR_LOG_STREAM,
        ]
        response = self.client.describe_log_streams(logGroupName=config.LOG_GROUP)
        existing_log_streams = [s["logStreamName"] for s in response["logStreams"]]

        for log_stream in log_streams:
            if log_stream not in existing_log_streams:
                self.client.create_log_stream(
                    logGroupName=config.LOG_GROUP, logStreamName=log_stream
                )

    def info(self, event):
        self._log_event(log_stream_name=config.INFO_LOG_STREAM, event=event)

    def error(self, event):
        self._log_event(log_stream_name=config.ERROR_LOG_STREAM, event=event)

    def status(self, event):
        self._log_event(log_stream_name=config.STATUS_LOG_STREAM, event=event)

    def peek_status(self):
        events = self._get_events(config.STATUS_LOG_STREAM, limit=1)

        if len(events) > 0:
            return json.loads(events[0]["message"])

        return None

    def _log_event(self, log_stream_name, event):
        self._log_events(log_stream_name, events=[event])

    def _log_events(self, log_stream_name, events):
        for event in events:
            if "timestamp" not in event:
                event["timestamp"] = utils.get_timestamp_millis()

        self.client.put_log_events(
            logGroupName=config.LOG_GROUP,
            logStreamName=log_stream_name,
            logEvents=events,
        )

    def _get_events(self, log_stream_name, limit=100):
        response = self.client.get_log_events(
            logGroupName=config.LOG_GROUP,
            logStreamName=log_stream_name,
            limit=limit,
        )

        return response["events"]
