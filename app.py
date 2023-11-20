import boto3
from chalice import Chalice

# Load environment variables from .env files.
from dotenv import find_dotenv, load_dotenv

# Import the modules from the chalicelib directory.
from chalicelib import dlq, events, persistence, services

# Load environment variables before initializing the application.
load_dotenv(find_dotenv())

# Create a new Chalice application instance.
app = Chalice(app_name="daily-ai-coding-task")

# Initialize AWS CloudWatch logs client for event logging.
event_logger = events.EventLogger(client=boto3.client("logs"))

# Initialize a Dead Letter Queue (DLQ) for handling message failures.
dead_letter_queue = dlq.DeadLetterQueue(
    sqs_resource=boto3.client("sqs"), event_logger=event_logger
)

# Set up the DynamoDB table for user data persistence.
users_table = persistence.UsersTable(
    dynamo_resource=boto3.resource("dynamodb"), event_logger=event_logger
)

# Initialize the data fetching service with the necessary components.
data_fetcher = services.DataFetcher(
    event_logger=event_logger, users_table=users_table, dlq=dead_letter_queue
)


# Define a Chalice route to fetch data when a POST request is made to /fetch-data.
@app.route("/fetch-data", methods=["POST"])
def fetch_data():
    # Fetch data using the data_fetcher service and return the status.
    status = data_fetcher.fetch()
    return status


# Define a Chalice route to retrieve and view data with a GET request to /view-data.
@app.route("/view-data", methods=["GET"])
def view_data():
    # Get data from the data_fetcher service and return it.
    data = data_fetcher.get()
    return data


# Define a Chalice route for checking the status of the data fetcher with a GET request to /status.
@app.route("/status", methods=["GET"])
def status():
    # Retrieve and return the current status from the data_fetcher service.
    status = data_fetcher.status()
    return status
