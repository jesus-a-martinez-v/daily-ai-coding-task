import boto3
from dotenv import find_dotenv
from dotenv import load_dotenv

# TODO RENAME THESE
import json
from config import ERROR_LOG_STREAM_NAME
from config import FETCHES_LOG_STREAM_NAME
from config import INFO_LOG_STREAM_NAME
from config import LOG_GROUP_NAME
from config import RETENTION_PERIOD_IN_DAYS
from utils import get_timestamp

load_dotenv(find_dotenv())


class EventLogger:
    def __init__(self):
        try:
            self.client = boto3.client("logs")
            self._create_log_group()
            self._create_log_streams()
        except Exception as e:
            print("[FATAL] Could not initialize EventLogger", e)
            raise

    def _create_log_group(self):
        exists = False

        response = self.client.describe_log_groups(logGroupNamePrefix=LOG_GROUP_NAME)

        for each_line in response["logGroups"]:
            if LOG_GROUP_NAME == each_line["logGroupName"]:
                exists = True
                break

        if not exists:
            self.client.create_log_group(
                logGroupName=LOG_GROUP_NAME,
                tags={
                    "Frequency": "30 seconds",
                    "Environment": "Development",
                    "RetentionPeriod": str(RETENTION_PERIOD_IN_DAYS),
                    "Type": "Backend",
                },
            )

            self.client.put_retention_policy(
                logGroupName=LOG_GROUP_NAME, retentionInDays=RETENTION_PERIOD_IN_DAYS
            )

    def _create_log_streams(self):
        log_streams = [
            FETCHES_LOG_STREAM_NAME,
            INFO_LOG_STREAM_NAME,
            ERROR_LOG_STREAM_NAME,
        ]
        response = self.client.describe_log_streams(logGroupName=LOG_GROUP_NAME)
        existing_log_streams = [s["logStreamName"] for s in response["logStreams"]]

        for log_stream in log_streams:
            if log_stream not in existing_log_streams:
                self.client.create_log_stream(
                    logGroupName=LOG_GROUP_NAME, logStreamName=log_stream
                )

    def info(self, event):
        self._log_event(log_stream_name=INFO_LOG_STREAM_NAME, event=event)

    def error(self, event):
        self._log_event(log_stream_name=ERROR_LOG_STREAM_NAME, event=event)

    def status(self, event):
        self._log_event(log_stream_name=FETCHES_LOG_STREAM_NAME, event=event)

    def peek_status(self):
        events = self._get_events(FETCHES_LOG_STREAM_NAME, limit=1)

        if len(events) > 0:
            return json.loads(events[0]["message"])

        return None

    def _log_event(self, log_stream_name, event):
        self._log_events(log_stream_name, events=[event])

    def _log_events(self, log_stream_name, events):
        for event in events:
            if "timestamp" not in event:
                event["timestamp"] = get_timestamp()

        self.client.put_log_events(
            logGroupName=LOG_GROUP_NAME,
            logStreamName=log_stream_name,
            logEvents=events,
        )

    def _get_events(self, log_stream_name, limit=100):
        response = self.client.get_log_events(
            logGroupName=LOG_GROUP_NAME,
            logStreamName=log_stream_name,
            limit=limit,
        )

        return response["events"]
