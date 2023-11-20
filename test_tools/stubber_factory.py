from test_tools.cloudwatch_stubber import CloudWatchStubber
from test_tools.dynamodb_stubber import DynamoDBStubber
from test_tools.sqs_stubber import SqsStubber


class StubberFactoryNotImplemented(Exception):
    pass


def stubber_factory(service_name):
    if service_name == "logs":
        return CloudWatchStubber
    elif service_name == "dynamodb":
        return DynamoDBStubber
    elif service_name == "sqs":
        return SqsStubber
    else:
        raise StubberFactoryNotImplemented(
            "Make sure you added a new stubber to stubber_factory.py."
        )
