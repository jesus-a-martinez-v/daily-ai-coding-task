import json
from abc import ABC
from abc import abstractmethod
from decimal import Decimal

# Import the exception class to handle client errors from AWS SDK.
from botocore.exceptions import ClientError


# Define an abstract base class for a DynamoDB table.
class DynamoDbTable(ABC):
    def __init__(self, dynamo_resource, table_name, event_logger):
        # Initialize with AWS DynamoDB resource, table name, and an event logger.
        self.dynamo_resource = dynamo_resource
        self.table_name = table_name
        self.event_logger = event_logger
        self.table = None

    def exists(self):
        # Check if the table exists by trying to load it.
        try:
            self.table = self.dynamo_resource.Table(self.table_name)
            self.table.load()
            return True
        except ClientError as e:
            # If the table does not exist, log the error and return False.
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                return False
            else:
                # Log any other exceptions and re-raise them.
                self.event_logger.error(
                    event={
                        "message": json.dumps(
                            {
                                "message": f"Could not check for existence of {self.table_name}",
                                "error_code": e.response["Error"]["Code"],
                                "error_message": e.response["Error"]["Message"],
                            }
                        )
                    }
                )
                raise e

    def create_table(self):
        # Gather table creation parameters from the abstract methods.
        key_schema = self.get_key_schema()
        attribute_definitions = self.get_attribute_definitions()
        provisioned_throughput = self.get_provisioned_throughput()

        # Attempt to create the table with the specified parameters.
        try:
            self.table = self.dynamo_resource.create_table(
                TableName=self.table_name,
                KeySchema=key_schema,
                AttributeDefinitions=attribute_definitions,
                ProvisionedThroughput=provisioned_throughput,
            )
            # Wait until the table exists before proceeding.
            self.table.wait_until_exists()
        except Exception as e:
            # Log any exception during table creation and re-raise it.
            self.event_logger.error(
                event={
                    "message": f"Could not create table {self.table_name}. Error: {e}"
                }
            )
            raise e

    def add_elements(self, elements):
        # Batch insert elements into the table.
        try:
            with self.table.batch_writer() as w:
                for e in elements:
                    # Serialize each element before inserting it.
                    w.put_item(Item=self.serialize(e))

            # Log the successful addition of elements.
            self.event_logger.info(
                event={"message": f"Saved {len(elements)} into {self.table_name}"}
            )
        except Exception as e:
            # Log any exception during data insertion.
            self.event_logger.error(
                event={
                    "message": f"Couldn't save data into table {self.table_name}. Error: {e}",
                }
            )

    def get_elements(self):
        # Retrieve elements from the table.
        elements = []
        try:
            done = False
            start_key = None
            kwargs = {}

            # Continue scanning until there is no more data.
            while not done:
                if start_key:
                    kwargs["ExclusiveStartKey"] = start_key

                # Retrieve a batch of elements.
                response = self.table.scan(**kwargs)
                elements.extend(response.get("Items", []))
                start_key = response.get("LastEvaluatedKey", None)
                done = start_key is None

            return elements
        except ClientError as e:
            # Log any exception during retrieval and return an empty list.
            self.event_logger.error(
                event={
                    "message": json.dumps(
                        {
                            "message": f"Couldn't get elements from table {self.table_name}",
                            "error_code": e.response["Error"]["Code"],
                            "error_message": e.response["Error"]["Message"],
                        }
                    )
                }
            )
            return []

    # Define abstract methods that subclasses must implement.
    @abstractmethod
    def get_key_schema(self):
        pass

    @abstractmethod
    def get_attribute_definitions(self):
        pass

    @abstractmethod
    def serialize(self, element):
        pass

    @abstractmethod
    def get_provisioned_throughput(self):
        pass


# Implement a concrete class for a specific DynamoDB table.
class UsersTable(DynamoDbTable):
    def __init__(self, dynamo_resource, event_logger):
        # Initialize the UsersTable with the specific table name "users".
        super().__init__(dynamo_resource, "users", event_logger)

    # Return the key schema for the "users" table.
    def get_key_schema(self):
        return [
            {"AttributeName": "id", "KeyType": "HASH"},  # Partition key
            {"AttributeName": "last_name", "KeyType": "RANGE"},  # Sort key
        ]

    # Return the attribute definitions for the "users" table.
    def get_attribute_definitions(self):
        return [
            {"AttributeName": "id", "AttributeType": "N"},
            {"AttributeName": "last_name", "AttributeType": "S"},
        ]

    # Return the provisioned throughput settings for the "users" table.
    def get_provisioned_throughput(self):
        return {
            "ReadCapacityUnits": 1,
            "WriteCapacityUnits": 1,
        }

    # Serialize the given element for insertion into the DynamoDB "users" table.
    def serialize(self, element):
        # Convert the latitude and longitude to Decimal for DynamoDB compatibility.
        lat = element["address"]["coordinates"]["lat"]
        lng = element["address"]["coordinates"]["lng"]

        element["address"]["coordinates"] = {
            "lat": Decimal(str(lat)),
            "lng": Decimal(str(lng)),
        }

        return element
