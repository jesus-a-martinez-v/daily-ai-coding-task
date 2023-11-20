"""
Stub functions that are used by the Amazon DynamoDB unit tests.

When tests are run against an actual AWS account, the stubber class does not
set up stubs and passes all calls through to the Boto3 client.
"""

from decimal import Decimal
from botocore.stub import ANY

from test_tools.stubber import BaseStubber


class DynamoDBStubber(BaseStubber):
    """
    A class that implements a variety of stub functions that are used by the
    Amazon DynamoDB unit tests.

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

    type_encoding = {
        type(""): "S",
        type(1): "N",
        type(0.1): "N",
        type(Decimal()): "N",
        type(b""): "B",
        type({}): "M",
        type([]): "L",
        type(True): "BOOL",
    }

    @staticmethod
    def _add_table_schema(table_desc, table_name, schema):
        """Build a table schema from its parts."""
        table_desc["TableName"] = table_name
        table_desc["KeySchema"] = schema

    def _build_out_item(self, in_item):
        out_item = {}
        for key, value in in_item.items():
            if value is not None:
                value_type = self.type_encoding[type(value)]
                if value_type == "M":
                    out_val = self._build_out_item(value)
                elif value_type == "L":
                    out_val = [
                        {self.type_encoding[type(list_val)]: list_val}
                        for list_val in value
                    ]
                elif value_type == "BOOL":
                    out_val = value
                else:
                    out_val = str(value)
                out_item[key] = {value_type: out_val}
        return out_item

    def stub_create_table(
        self, table_name, schema, throughput, attribute_definitions, error_code=None
    ):
        table_input = {
            "ProvisionedThroughput": throughput,
            "AttributeDefinitions": attribute_definitions,
        }
        self._add_table_schema(table_input, table_name, schema)

        table_output = {"TableStatus": "CREATING"}
        self._add_table_schema(table_output, table_name, schema)
        self._stub_bifurcator(
            "create_table",
            table_input,
            {"TableDescription": table_output},
            error_code=error_code,
        )

    def stub_describe_table(
        self,
        table_name,
        schema=None,
        provisioned_throughput=None,
        status="ACTIVE",
        error_code=None,
    ):
        response = {"Table": {"TableStatus": status}}
        if schema is not None:
            self._add_table_schema(response["Table"], table_name, schema)
        if provisioned_throughput is not None:
            response["Table"]["ProvisionedThroughput"] = provisioned_throughput
        self._stub_bifurcator(
            "describe_table",
            expected_params={"TableName": table_name},
            response=response,
            error_code=error_code,
        )

    def stub_scan(
        self,
        table_name,
        output_items,
        select=None,
        filter_expression=None,
        projection_expression=None,
        expression_attrs=None,
        start_key=None,
        last_key=None,
        error_code=None,
    ):
        expected_params = {"TableName": table_name}
        if select:
            expected_params["Select"] = select
        if filter_expression:
            expected_params["FilterExpression"] = filter_expression
        if projection_expression:
            expected_params["ProjectionExpression"] = projection_expression
        if expression_attrs:
            expected_params["ExpressionAttributeNames"] = expression_attrs
        if start_key:
            expected_params["ExclusiveStartKey"] = start_key
        response = {
            "Items": [self._build_out_item(output_item) for output_item in output_items]
        }
        if last_key:
            response["LastEvaluatedKey"] = last_key
        self._stub_bifurcator("scan", expected_params, response, error_code=error_code)

    def stub_batch_write_item(
        self, request_items, unprocessed_items=None, error_code=None
    ):
        expected_params = {"RequestItems": request_items}
        response = {
            "UnprocessedItems": unprocessed_items
            if unprocessed_items is not None
            else {}
        }
        self._stub_bifurcator(
            "batch_write_item", expected_params, response, error_code=error_code
        )
