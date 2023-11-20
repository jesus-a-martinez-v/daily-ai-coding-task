import json
import random
from datetime import datetime

# Import exceptions to handle specific AWS SDK client errors.
from botocore.exceptions import ClientError
from botocore.exceptions import NoRegionError

# Import a custom session class for rate limiting API calls.
from requests_ratelimiter import LimiterSession

# Import local configuration settings and utility functions.
from . import config
from . import utils


# Define a class to manage data fetching operations.
class DataFetcher:
    def __init__(self, event_logger, users_table, dlq):
        try:
            # Initialize fetch status and various components needed for the data fetch.
            self.current_fetch_status = self._reset_fetch_status()
            self.event_logger = event_logger
            self.dlq = dlq
            self.limiter_session = LimiterSession(
                per_minute=config.API_CALLS_PER_MINUTE
            )
            self.users = users_table

            # Ensure the users table exists or create it.
            if not self.users.exists():
                self.users.create_table()
        except Exception as e:
            # Log a fatal error if initialization fails and re-raise the exception.
            error_event = {
                "message": "[FATAL] Could not create Data Fetcher",
                "error_message": str(e),
            }

            self.event_logger(event={"message": json.dumps(error_event)})
            raise e

    def fetch(self):
        # Reset the fetch status and record the start time.
        self.current_fetch_status = self._reset_fetch_status()
        start = datetime.now()

        # Determine the number of API calls to make based on configuration settings.
        number_of_calls = random.randint(*config.USERS_CALLS_PER_FETCH)
        for i in range(number_of_calls):
            # Log the commencement of each API call.
            self.event_logger.info(
                event={
                    "message": f"Performing call {i + 1}/{number_of_calls}",
                }
            )

            # Get data from the API.
            data = self._get_data(config.USERS_ENDPOINT)

            # Update fetch status with the number of users fetched.
            self.current_fetch_status["users"] += len(data)

            # Add fetched data to the users table.
            self.users.add_elements(data)

        # Calculate and record the time taken for the fetch operation.
        elapsed = datetime.now() - start
        self.current_fetch_status["duration"] = elapsed.total_seconds()

        # Log the status of the fetch operation.
        self.event_logger.status(
            event={"message": json.dumps(self.current_fetch_status)}
        )

        # Return the current fetch status.
        return self.current_fetch_status

    def _get_data(self, endpoint):
        # Increment the API call count in fetch status.
        self.current_fetch_status["api_calls"] += 1
        # Set parameters for the API call.
        params = {"size": random.randint(*config.USERS_PER_API_CALL)}

        try:
            # Make a rate-limited API call.
            response = self.limiter_session.get(endpoint, params=params)

            # Handle non-200 status codes.
            if response.status_code != 200:
                error_event = {
                    "message": f"Received {response.status_code} code, but expected 200",
                    "response_code": response.status_code,
                    "response_content": response.text,
                }

                # Log the error and send it to the dead letter queue.
                self.current_fetch_status["errors"].append(error_event)
                self.event_logger.error(event={"message": json.dumps(error_event)})
                self.dlq.send(message=error_event)

                return []

            # Parse the response data.
            data = response.json()

            # Handle unexpected data in the response.
            if "message" in data and data["message"] == "Maximum allowed size is 100":
                error_event = {
                    "host": endpoint,
                    "message": "An unexpected error occurred when fetching users.",
                    "response": response.status_code,
                    "response_content": response.text,
                }

                # Log the error and send it to the dead letter queue.
                self.current_fetch_status["errors"].append(error_event)
                self.event_logger.error(event={"message": json.dumps(error_event)})
                self.dlq.send(message=error_event)

                return []

            # Log the successful retrieval of data.
            self.event_logger.info(
                event={
                    "message": f"Fetched {len(data)} users successfully.",
                }
            )

            return data
        except Exception as e:
            # Log any exceptions that occur during the API call.
            error_event = {
                "message": f"An unexpected Runtime error occurred.",
                "error": str(e),
                "params": params,
                "host": endpoint,
            }
            self.event_logger.error(event={"message": json.dumps(error_event)})
            self.dlq.send(message=error_event)
            return []

    @staticmethod
    def _reset_fetch_status():
        # Reset the fetch status to default values.
        return {
            "users": 0,
            "api_calls": 0,
            "errors": [],
            "timestamp": utils.get_timestamp_millis(),
            "duration": 0.0,
        }

    def status(self):
        # Retrieve the current status from the event logger.
        return self.event_logger.peek_status()

    def get(self):
        # Retrieve elements from the users table.
        try:
            return self.users.get_elements()
        except Exception as e:
            # Return an empty list if an exception occurs.
            return []
