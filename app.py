import boto3
from chalice import Chalice
from dotenv import find_dotenv
from dotenv import load_dotenv

from chalicelib import persistence
from chalicelib import events
from chalicelib import services

load_dotenv(find_dotenv())


app = Chalice(app_name="daily-ai-coding-task")

event_logger = events.EventLogger(client=boto3.client("logs"))
users_table = persistence.UsersTable(
    dynamo_resource=boto3.resource("dynamodb"), event_logger=event_logger
)
data_fetcher = services.DataFetcher(event_logger=event_logger, users_table=users_table)


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
