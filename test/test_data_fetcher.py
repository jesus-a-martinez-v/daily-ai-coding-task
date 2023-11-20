# Import necessary libraries and modules
import boto3
import pytest

# Import custom modules from the chalicelib directory
from chalicelib import config
from chalicelib.events import EventLogger
from chalicelib.persistence import UsersTable
from chalicelib.services import DataFetcher


# Define a parameterized test for the DataFetcher creation process
@pytest.mark.parametrize("error", [None, "TestError"])
def test_data_fetcher_create(make_stubber, error):
    # Initialize AWS CloudWatch logs client and stubber for testing
    cloudwatch_resource = boto3.client("logs", region_name="us-west-1")
    cloudwatch_stubber = make_stubber(cloudwatch_resource)
    # Stub AWS CloudWatch log group and stream descriptions for the test
    cloudwatch_stubber.stub_describe_log_groups()
    cloudwatch_stubber.stub_describe_log_streams()
    # Create an instance of EventLogger with the CloudWatch logs client
    el = EventLogger(client=cloudwatch_resource)

    # Initialize AWS DynamoDB resource and stubber for testing
    dynamo_resource = boto3.resource("dynamodb", region_name="us-west-1")
    dynamo_stubber = make_stubber(dynamo_resource.meta.client)

    # Create an instance of UsersTable without an actual table to test table creation
    users_table = UsersTable(dynamo_resource=dynamo_resource, event_logger=el)
    # Assert that the UsersTable instance does not have an existing table
    assert users_table.table is None

    # If there is no error parameter, stub the describe table operation
    if not error:
        dynamo_stubber.stub_describe_table(
            table_name="users",
            schema=users_table.get_key_schema(),
            provisioned_throughput=users_table.get_provisioned_throughput(),
        )
        # Attempt to create a DataFetcher instance without errors
        DataFetcher(event_logger=el, dlq=None, users_table=users_table)
    else:
        # If there is an error, stub CloudWatch logs to simulate error logging
        cloudwatch_stubber.stub_put_log_events(
            log_group_name=config.LOG_GROUP,
            log_stream_name=config.ERROR_LOG_STREAM,
        )
        # Stub the describe table operation to simulate an error
        dynamo_stubber.stub_describe_table(
            table_name="users",
            schema=users_table.get_key_schema(),
            provisioned_throughput=users_table.get_provisioned_throughput(),
            error_code=error,
        )
        # Expect an exception when creating a DataFetcher instance with errors
        with pytest.raises(Exception):
            DataFetcher(event_logger=el, dlq=None, users_table=users_table)


# Similar to the test_data_fetcher_create function, this is a parameterized test
# for the 'get' method of the DataFetcher class
@pytest.mark.parametrize("error", [None, "TestError"])
def test_data_get(make_stubber, error):
    # Setup AWS CloudWatch and DynamoDB resources and stubbers as before
    cloudwatch_resource = boto3.client("logs", region_name="us-west-1")
    cloudwatch_stubber = make_stubber(cloudwatch_resource)
    cloudwatch_stubber.stub_describe_log_groups()
    cloudwatch_stubber.stub_describe_log_streams()

    el = EventLogger(client=cloudwatch_resource)

    dynamo_resource = boto3.resource("dynamodb", region_name="us-west-1")
    dynamo_stubber = make_stubber(dynamo_resource.meta.client)

    users_table = UsersTable(dynamo_resource=dynamo_resource, event_logger=el)

    # Stub DynamoDB describe table operation
    dynamo_stubber.stub_describe_table(
        table_name="users",
        schema=users_table.get_key_schema(),
        provisioned_throughput=users_table.get_provisioned_throughput(),
    )

    # Create a DataFetcher instance
    df = DataFetcher(event_logger=el, dlq=None, users_table=users_table)

    # Define a mock item to simulate a database entry
    item = {
        "id": 1,
        "last_name": "Smith",
        "address": {"coordinates": {"lat": 1.0, "lng": 2.0}},
    }
    # If there is no error, stub the DynamoDB scan operation to return the mock item
    if not error:
        dynamo_stubber.stub_scan(
            table_name="users",
            output_items=[item],
        )
        # Perform a get operation and assert that it returns results
        results = df.get()
        assert len(results) > 0
    else:
        # If there is an error, stub the scan operation to simulate an error
        dynamo_stubber.stub_scan(
            table_name="users",
            output_items=[item],
            error_code=error,
        )
        # Stub CloudWatch to simulate error logging
        cloudwatch_stubber.stub_put_log_events(
            log_group_name=config.LOG_GROUP,
            log_stream_name=config.ERROR_LOG_STREAM,
        )
        # Perform a get operation and assert that it returns no results
        results = df.get()
        assert len(results) == 0


# Define a test for checking the status of the DataFetcher
def test_data_fetcher_status(make_stubber):
    # Setup AWS CloudWatch and DynamoDB resources and stubbers as in previous tests
    cloudwatch_resource = boto3.client("logs", region_name="us-west-1")
    cloudwatch_stubber = make_stubber(cloudwatch_resource)
    cloudwatch_stubber.stub_describe_log_groups()
    cloudwatch_stubber.stub_describe_log_streams()

    el = EventLogger(client=cloudwatch_resource)

    dynamo_resource = boto3.resource("dynamodb", region_name="us-west-1")
    dynamo_stubber = make_stubber(dynamo_resource.meta.client)

    # Stub DynamoDB operations to simulate table creation and description
    users_table = UsersTable(dynamo_resource=dynamo_resource, event_logger=el)
    dynamo_stubber.stub_describe_table(
        table_name="users",
        error_code="ResourceNotFoundException",
    )
    dynamo_stubber.stub_create_table(
        table_name="users",
        schema=users_table.get_key_schema(),
        throughput=users_table.get_provisioned_throughput(),
        attribute_definitions=users_table.get_attribute_definitions(),
    )
    dynamo_stubber.stub_describe_table(
        table_name="users",
        schema=users_table.get_key_schema(),
        provisioned_throughput=users_table.get_provisioned_throughput(),
    )

    # Create a DataFetcher instance
    df = DataFetcher(event_logger=el, dlq=None, users_table=users_table)

    # Stub CloudWatch to simulate fetching log events
    cloudwatch_stubber.stub_get_log_events(
        log_group_name=config.LOG_GROUP,
        log_stream_name=config.STATUS_LOG_STREAM,
        limit=1,
        empty_response=False,
    )
    # Get the status from DataFetcher and assert the expected values
    status = df.status()
    assert status["users"] == 42
    assert status["api_calls"] == 2
    assert len(status["errors"]) == 0
    assert status["timestamp"] == 1700410240494
    assert status["duration"] == 1.23
