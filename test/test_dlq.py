# Import necessary libraries
import boto3
import pytest

# Import custom modules from the chalicelib directory
from chalicelib import config
from chalicelib.dlq import DeadLetterQueue
from chalicelib.events import EventLogger


# Define a parameterized test for DeadLetterQueue creation with different scenarios
@pytest.mark.parametrize(
    "dlq_exists,error", [(True, None), (False, None), (False, "TestError")]
)
def test_dlq_creation(make_stubber, dlq_exists, error):
    # Setup AWS CloudWatch logs client for logging
    cloudwatch_resource = boto3.client("logs", region_name="us-west-1")
    # Create a stubber for CloudWatch to mock AWS responses
    cloudwatch_stubber = make_stubber(cloudwatch_resource)
    # Stub the description of log groups and streams for testing
    cloudwatch_stubber.stub_describe_log_groups()
    cloudwatch_stubber.stub_describe_log_streams()

    # Instantiate the EventLogger with the CloudWatch client
    el = EventLogger(client=cloudwatch_resource)

    # Setup AWS SQS client for queue management
    sqs_resource = boto3.client("sqs", region_name="us-west-1")
    # Create a stubber for SQS to mock AWS responses
    sqs_stubber = make_stubber(sqs_resource)

    # If there is an error, we stub the log events and the SQS queue listing with an error
    if error:
        cloudwatch_stubber.stub_put_log_events(
            log_group_name=config.LOG_GROUP,
            log_stream_name=config.ERROR_LOG_STREAM,
        )
        sqs_stubber.stub_list_queues(
            urls=["my_existing_queue"], prefix="dlq", error_code=error
        )
        # Attempt to create a DeadLetterQueue instance which should fail
        DeadLetterQueue(sqs_resource, el)
    else:
        # If the dead letter queue exists, we stub the queue listing
        if dlq_exists:
            sqs_stubber.stub_list_queues(urls=["my_existing_queue"], prefix="dlq")
            # Create the DeadLetterQueue instance and assert the queue URL
            d = DeadLetterQueue(sqs_resource, el)
            assert d.queue_url == "my_existing_queue"
        else:
            # If the queue doesn't exist, we stub the queue listing and queue creation
            sqs_stubber.stub_list_queues(urls=[], prefix="dlq")
            sqs_stubber.stub_create_queue(
                name="dlq", attributes={}, url="my_created_queue"
            )
            # Stub the log events
            cloudwatch_stubber.stub_put_log_events()

            # Create the DeadLetterQueue instance and assert the queue URL of the created queue
            d = DeadLetterQueue(sqs_resource, el)
            assert d.queue_url == "my_created_queue"


# Define a parameterized test for the 'send' method of the DeadLetterQueue
@pytest.mark.parametrize("error", [None, "TestError"])
def test_dlq_send(make_stubber, error):
    # Setup AWS CloudWatch logs and SQS clients and stubbers
    cloudwatch_resource = boto3.client("logs", region_name="us-west-1")
    cloudwatch_stubber = make_stubber(cloudwatch_resource)
    cloudwatch_stubber.stub_describe_log_groups()
    cloudwatch_stubber.stub_describe_log_streams()

    # Instantiate the EventLogger with the CloudWatch client
    el = EventLogger(client=cloudwatch_resource)

    # Setup AWS SQS client for queue management
    sqs_resource = boto3.client("sqs", region_name="us-west-1")
    # Create a stubber for SQS to mock AWS responses
    sqs_stubber = make_stubber(sqs_resource)
    # Stub the SQS queue listing to return an existing queue
    sqs_stubber.stub_list_queues(urls=["my_existing_queue"], prefix="dlq")
    # Create the DeadLetterQueue instance
    d = DeadLetterQueue(sqs_resource, el)

    # If there is an error, we stub the send message operation to simulate a failure
    if error:
        cloudwatch_stubber.stub_put_log_events(
            log_group_name=config.LOG_GROUP,
            log_stream_name=config.ERROR_LOG_STREAM,
        )
        sqs_stubber.stub_send_message(
            url="my_existing_queue",
            body="""{"message": "Body message"}""",
            message_id="123",
            attributes={},
            error_code=error,
        )
    else:
        # If there is no error, we stub the log events and the send message operation
        cloudwatch_stubber.stub_put_log_events(
            log_group_name=config.LOG_GROUP,
            log_stream_name=config.INFO_LOG_STREAM,
        )
        sqs_stubber.stub_send_message(
            url="my_existing_queue",
            body="""{"message": "Body message"}""",
            message_id="123",
            attributes={},
        )

    # Attempt to send a message using the DeadLetterQueue instance
    d.send(message={"message": "Body message"})
