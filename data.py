from abc import ABC
from abc import abstractmethod
from decimal import Decimal

from botocore.exceptions import ClientError


class DynamoDbTable(ABC):
    def __init__(self, dynamo_resource, table_name, event_logger):
        self.dynamo_resource = dynamo_resource
        self.table_name = table_name
        self.event_logger = event_logger
        self.table = None

    def exists(self):
        try:
            self.table = self.dynamo_resource.Table(self.table_name)
            self.table.load()
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                return False
            else:
                self.event_logger.error(
                    event={
                        "message": f"Could not check for existence of {self.table_name}",
                        "error_code": e.response["Error"]["Code"],
                        "error_message": e.response["Error"]["Message"],
                    }
                )
                raise

    def create_table(self):
        key_schema = self.get_key_schema()
        attribute_definitions = self.get_attribute_definitions()
        provisioned_throughput = self.get_provisioned_throughput()

        try:
            self.table = self.dynamo_resource.create_table(
                TableName=self.table_name,
                KeySchema=key_schema,
                AttributeDefinitions=attribute_definitions,
                ProvisionedThroughput=provisioned_throughput,
            )
            self.table.wait_until_exists()
        except Exception as e:
            self.event_logger.error(
                event={
                    "message": f"Could not create table {self.table_name}. Error: {e}"
                }
            )
            raise

    def add_elements(self, elements):
        try:
            with self.table.batch_writer() as w:
                for e in elements:
                    w.put_item(Item=self.serialize(e))

            self.event_logger.info(
                event={"message": f"Saved {len(elements)} into {self.table_name}"}
            )
        except Exception as e:
            self.event_logger.error(
                event={
                    "message": f"Couldn't save data into table {self.table_name}. Error: {e}",
                }
            )

    def get_elements(self):
        elements = []
        try:
            done = False
            start_key = None
            kwargs = {}

            while not done:
                if start_key:
                    kwargs["ExclusiveStartKey"] = start_key

                # This is an expensive operation.
                # Improvement: Add filters
                response = self.table.scan(**kwargs)
                elements.extend(response.get("Items", []))
                start_key = response.get("LastEvaluatedKey", None)
                done = start_key is None

            return elements
        except ClientError as e:
            self.event_logger.error(
                event={
                    "message": f"Couldn't get elements from table {self.table_name}",
                    "error_code": e.response["Error"]["Code"],
                    "error_message": e.response["Error"]["Message"],
                }
            )
            return []

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


class UsersTable(DynamoDbTable):
    def __init__(self, dynamo_resource, event_logger):
        super().__init__(dynamo_resource, "users", event_logger)

    def get_key_schema(self):
        return [
            {"AttributeName": "id", "KeyType": "HASH"},  # Partition key
            {"AttributeName": "last_name", "KeyType": "RANGE"},  # Sort key
        ]

    def get_attribute_definitions(self):
        return [
            {"AttributeName": "id", "AttributeType": "N"},
            {"AttributeName": "last_name", "AttributeType": "S"},
        ]

    def get_provisioned_throughput(self):
        return {
            "ReadCapacityUnits": 1,
            "WriteCapacityUnits": 1,
        }

    def serialize(self, element):
        lat = element["address"]["coordinates"]["lat"]
        lng = element["address"]["coordinates"]["lng"]

        element["address"]["coordinates"] = {
            "lat": Decimal(str(lat)),
            "lng": Decimal(str(lng)),
        }

        return element
