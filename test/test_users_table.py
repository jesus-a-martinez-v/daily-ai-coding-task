# Importing necessary libraries and modules
import boto3
import pytest
from botocore.exceptions import ClientError

# Import custom modules for configuration and utility classes
from chalicelib import config
from chalicelib.events import EventLogger
from chalicelib.persistence import UsersTable


# This test checks if a user table can be created with and without simulated errors.
@pytest.mark.parametrize("error", [None, "TestError"])
def test_users_table_create(make_stubber, error):
    # Setup AWS CloudWatch and DynamoDB clients for the test.
    cloudwatch_resource = boto3.client("logs", region_name="us-west-1")
    cloudwatch_stubber = make_stubber(cloudwatch_resource)
    cloudwatch_stubber.stub_describe_log_groups()
    cloudwatch_stubber.stub_describe_log_streams()
    el = EventLogger(client=cloudwatch_resource)

    dynamo_resource = boto3.resource("dynamodb", region_name="us-west-1")
    dynamo_stubber = make_stubber(dynamo_resource.meta.client)

    # Initialize the UsersTable class, which should not have an associated table yet.
    users_table = UsersTable(dynamo_resource=dynamo_resource, event_logger=el)
    assert users_table.table is None

    # If no error is simulated, stub the creation of the table and confirm it exists afterwards.
    if not error:
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

        users_table.create_table()
        assert users_table.table is not None
    else:
        # If an error is simulated, stub the creation with an error and check that an exception is raised.
        cloudwatch_stubber.stub_put_log_events(
            log_group_name=config.LOG_GROUP,
            log_stream_name=config.ERROR_LOG_STREAM,
        )
        dynamo_stubber.stub_create_table(
            table_name="users",
            schema=users_table.get_key_schema(),
            throughput=users_table.get_provisioned_throughput(),
            attribute_definitions=users_table.get_attribute_definitions(),
            error_code=error,
        )

        with pytest.raises(Exception):
            users_table.create_table()


# This test verifies the existence of the user table with various simulated errors.
@pytest.mark.parametrize("error", [None, "ResourceNotFoundException", "TestError"])
def test_users_table_exist(make_stubber, error):
    # Similar setup for CloudWatch and DynamoDB clients as the previous test.
    cloudwatch_resource = boto3.client("logs", region_name="us-west-1")
    cloudwatch_stubber = make_stubber(cloudwatch_resource)
    cloudwatch_stubber.stub_describe_log_groups()
    cloudwatch_stubber.stub_describe_log_streams()
    el = EventLogger(client=cloudwatch_resource)

    dynamo_resource = boto3.resource("dynamodb", region_name="us-west-1")
    dynamo_stubber = make_stubber(dynamo_resource.meta.client)
    users_table = UsersTable(dynamo_resource=dynamo_resource, event_logger=el)

    # Check if the table exists without error, expect true.
    if not error:
        dynamo_stubber.stub_describe_table(
            table_name="users",
            schema=users_table.get_key_schema(),
            provisioned_throughput=users_table.get_provisioned_throughput(),
        )
        result = users_table.exists()
        assert result is True
    elif error == "ResourceNotFoundException":
        # If a 'ResourceNotFoundException' is simulated, stub the response and expect false.
        dynamo_stubber.stub_describe_table(
            table_name="users",
            error_code=error,
        )
        result = users_table.exists()
        assert result is False
    else:
        # For any other simulated error, stub the error and expect a ClientError exception.
        cloudwatch_stubber.stub_put_log_events(
            log_group_name=config.LOG_GROUP,
            log_stream_name=config.ERROR_LOG_STREAM,
        )
        dynamo_stubber.stub_describe_table(
            table_name="users",
            error_code=error,
        )

        with pytest.raises(ClientError):
            users_table.exists()


# This test checks if elements can be added to the user table with and without simulated errors.
@pytest.mark.parametrize("error", [None, "TestError"])
def test_users_table_add_elements(make_stubber, error):
    # Setup for AWS clients is identical to previous tests.
    cloudwatch_resource = boto3.client("logs", region_name="us-west-1")
    cloudwatch_stubber = make_stubber(cloudwatch_resource)
    cloudwatch_stubber.stub_describe_log_groups()
    cloudwatch_stubber.stub_describe_log_streams()
    el = EventLogger(client=cloudwatch_resource)

    dynamo_resource = boto3.resource("dynamodb", region_name="us-west-1")
    dynamo_stubber = make_stubber(dynamo_resource.meta.client)

    users_table = UsersTable(dynamo_resource=dynamo_resource, event_logger=el)

    # Create the users table for this test.
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
    users_table.create_table()
    assert users_table.table is not None

    # Define a sample item to add to the table.
    item = {
        "id": 1,
        "last_name": "Smith",
        "address": {"coordinates": {"lat": 1.0, "lng": 2.0}},
    }
    # Prepare the request format for DynamoDB batch writing.
    request_items = {"users": [{"PutRequest": {"Item": users_table.serialize(item)}}]}

    # If no error is simulated, stub the batch write operation and add the item.
    if not error:
        dynamo_stubber.stub_batch_write_item(request_items=request_items)

        cloudwatch_stubber.stub_put_log_events(
            log_group_name=config.LOG_GROUP,
            log_stream_name=config.INFO_LOG_STREAM,
        )

        users_table.add_elements([item])
    else:
        # If an error is simulated, stub the batch write with an error.
        dynamo_stubber.stub_batch_write_item(
            request_items=request_items,
            error_code=error,
        )
        cloudwatch_stubber.stub_put_log_events(
            log_group_name=config.LOG_GROUP,
            log_stream_name=config.ERROR_LOG_STREAM,
        )
        users_table.add_elements([item])


# This test checks if elements can be retrieved from the user table with and without simulated errors.
@pytest.mark.parametrize("error", [None, "TestError"])
def test_users_table_get_elements(make_stubber, error):
    # AWS client setup is the same as before.
    cloudwatch_resource = boto3.client("logs", region_name="us-west-1")
    cloudwatch_stubber = make_stubber(cloudwatch_resource)
    cloudwatch_stubber.stub_describe_log_groups()
    cloudwatch_stubber.stub_describe_log_streams()
    el = EventLogger(client=cloudwatch_resource)

    dynamo_resource = boto3.resource("dynamodb", region_name="us-west-1")
    dynamo_stubber = make_stubber(dynamo_resource.meta.client)

    users_table = UsersTable(dynamo_resource=dynamo_resource, event_logger=el)

    # Create the users table for this test.
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
    users_table.create_table()
    assert users_table.table is not None

    # Define a sample item to be retrieved.
    item = {
        "id": 1,
        "last_name": "Smith",
        "address": {"coordinates": {"lat": 1.0, "lng": 2.0}},
    }
    # If no error is simulated, stub the scan operation to return the item and verify retrieval.
    if not error:
        dynamo_stubber.stub_scan(
            table_name="users",
            output_items=[item],
        )
        results = users_table.get_elements()
        assert len(results) > 0
    else:
        # If an error is simulated, stub the scan operation with an error and verify no retrieval.
        dynamo_stubber.stub_scan(
            table_name="users",
            output_items=[item],
            error_code=error,
        )
        cloudwatch_stubber.stub_put_log_events(
            log_group_name=config.LOG_GROUP,
            log_stream_name=config.ERROR_LOG_STREAM,
        )
        results = users_table.get_elements()
        assert len(results) == 0
