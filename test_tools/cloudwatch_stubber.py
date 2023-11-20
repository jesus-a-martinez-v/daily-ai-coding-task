from botocore import stub

from chalicelib import config
from test_tools.stubber import BaseStubber
import json


class CloudWatchStubber(BaseStubber):
    """
    A class that implements stub functions used by Amazon CloudWatch unit tests.

    The stubbed functions expect certain parameters to be passed to them as
    part of the tests, and raise errors if the parameters are not as expected.
    """

    def __init__(self, client, use_stubs=True):
        """
        Initializes the object with a specific client and configures it for
        stubbing or AWS passthrough.
        """
        super().__init__(client, use_stubs)

    def stub_describe_log_groups(
        self, log_group_name_prefix=config.LOG_GROUP, error_code=None
    ):
        expected_params = {"logGroupNamePrefix": log_group_name_prefix}
        response = {"logGroups": [{"logGroupName": log_group_name_prefix}]}
        self._stub_bifurcator(
            "describe_log_groups", expected_params, response, error_code=error_code
        )

    def stub_describe_log_streams(
        self, log_group_name=config.LOG_GROUP, error_code=None
    ):
        expected_params = {"logGroupName": log_group_name}
        response = {
            "logStreams": [
                {"logStreamName": config.STATUS_LOG_STREAM},
                {"logStreamName": config.ERROR_LOG_STREAM},
                {"logStreamName": config.INFO_LOG_STREAM},
            ]
        }
        self._stub_bifurcator(
            "describe_log_streams", expected_params, response, error_code=error_code
        )

    def stub_get_log_events(
        self,
        log_group_name,
        log_stream_name,
        limit,
        empty_response=None,
        error_code=None,
    ):
        expected_params = {
            "logGroupName": log_group_name,
            "logStreamName": log_stream_name,
            "limit": limit,
        }

        if empty_response:
            response = {"events": []}
        else:
            response = {
                "events": [
                    {
                        "message": json.dumps(
                            {
                                "users": 42,
                                "api_calls": 2,
                                "errors": [],
                                "timestamp": 1700410240494,
                                "duration": 1.23,
                            }
                        )
                    }
                ]
            }

        self._stub_bifurcator(
            "get_log_events", expected_params, response, error_code=error_code
        )

    def stub_put_log_events(
        self, log_group_name=None, log_stream_name=None, log_events=None
    ):
        expected_params = {
            "logGroupName": stub.ANY,
            "logStreamName": stub.ANY,
            "logEvents": stub.ANY,
        }
        if log_group_name is not None:
            expected_params["logGroupName"] = log_group_name

        if log_stream_name is not None:
            expected_params["logStreamName"] = log_stream_name

        if log_events is not None:
            expected_params["logEvents"] = log_events

        self._stub_bifurcator(
            "put_log_events", expected_params, response=None, error_code=None
        )
