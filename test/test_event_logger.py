# Import necessary libraries
import boto3
import pytest

# Import configurations and EventLogger class from chalicelib directory
from chalicelib import config
from chalicelib.events import EventLogger


# Parameterize a test case to check the status of logs with both empty and non-empty responses
@pytest.mark.parametrize("empty_response", [True, False])
def test_peek_status(make_stubber, empty_response):
    # Initialize a CloudWatch logs client for a specific AWS region
    cloudwatch_resource = boto3.client("logs", region_name="us-west-1")
    # Create a stubber for the CloudWatch client to simulate AWS service responses
    cloudwatch_stubber = make_stubber(cloudwatch_resource)
    # Stub AWS CloudWatch log group and stream descriptions for the test setup
    cloudwatch_stubber.stub_describe_log_groups()
    cloudwatch_stubber.stub_describe_log_streams()
    # Stub the 'get_log_events' CloudWatch method to return either an empty response or a predefined log event
    cloudwatch_stubber.stub_get_log_events(
        log_group_name=config.LOG_GROUP,
        log_stream_name=config.STATUS_LOG_STREAM,
        limit=1,
        empty_response=empty_response,
    )

    # Instantiate an EventLogger with the CloudWatch logs client
    event_logger = EventLogger(client=cloudwatch_resource)

    # Use the EventLogger to peek at the status from the logs
    status = event_logger.peek_status()

    # If the stub was set to return an empty response, assert that the status is None
    if empty_response:
        assert status is None
    else:
        # If the stub was set to return a non-empty response, assert that the status contains expected data
        assert status["users"] == 42
        assert status["api_calls"] == 2
        assert len(status["errors"]) == 0
        assert status["timestamp"] == 1700410240494
        assert status["duration"] == 1.23
