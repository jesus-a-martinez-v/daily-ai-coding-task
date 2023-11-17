from chalice import Chalice

from data import UsersTable

# from dotenv import load_dotenv
# from dotenv import find_dotenv
# load_dotenv(find_dotenv())
from logs import EventLogger
from services import DataFetcher
import boto3


app = Chalice(app_name="daily-ai-coding-task")
event_logger = EventLogger(client=boto3.client("logs"))
users_table = UsersTable(
    dynamo_resource=boto3.resource("dynamodb"), event_logger=event_logger
)
data_fetcher = DataFetcher(event_logger=event_logger, users_table=users_table)


@app.route("/fetch-data", methods=["POST"])
def fetch_data():
    status = data_fetcher.fetch()
    return status


@app.route("/view-data", methods=["GET"])
def view_data():
    data = data_fetcher.get()
    return data


@app.route("/status", methods=["GET"])
def status():
    status = data_fetcher.status()
    return status
