"""
Stub functions that are used by the Amazon SQS unit tests.

When tests are run against an actual AWS account, the stubber class does not
set up stubs and passes all calls through to the Boto 3 client.
"""

from botocore.stub import ANY

from test_tools.stubber import BaseStubber


class SqsStubber(BaseStubber):
    """
    A class that implements a variety of stub functions that are used by the
    Amazon SQS unit tests.

    The stubbed functions all expect certain parameters to be passed to them as
    part of the tests, and will raise errors when the actual parameters differ from
    the expected.
    """

    def __init__(self, client, use_stubs=True):
        """
        Initializes the object with a specific client and configures it for
        stubbing or AWS passthrough.
        """
        super().__init__(client, use_stubs)

    def stub_create_queue(self, name, attributes, url, error_code=None):
        expected_params = {"QueueName": name, "Attributes": attributes}
        response = {"QueueUrl": url}
        self._stub_bifurcator(
            "create_queue", expected_params, response, error_code=error_code
        )

    def stub_list_queues(self, urls, prefix=None, max_results=1, error_code=None):
        expected_params = (
            {"QueueNamePrefix": prefix, "MaxResults": max_results} if prefix else {}
        )
        response = {"QueueUrls": urls}
        self._stub_bifurcator(
            "list_queues", expected_params, response, error_code=error_code
        )

    def stub_send_message(self, url, body, attributes, message_id, error_code=None):
        expected_params = {
            "QueueUrl": url,
            "MessageBody": body,
            "MessageAttributes": attributes,
        }
        response = {"MessageId": message_id}
        self._stub_bifurcator(
            "send_message", expected_params, response, error_code=error_code
        )

    def stub_set_queue_attributes(self, queue_url, attributes, error_code=None):
        expected_params = {"QueueUrl": queue_url, "Attributes": attributes}
        self._stub_bifurcator(
            "set_queue_attributes", expected_params, error_code=error_code
        )
