import json
import random
from datetime import datetime

from botocore.exceptions import ClientError
from botocore.exceptions import NoRegionError
from requests_ratelimiter import LimiterSession

from . import config
from . import utils


class DataFetcher:
    def __init__(self, event_logger, users_table):
        try:
            self.current_fetch_status = self._reset_fetch_status()
            self.event_logger = event_logger
            self.limiter_session = LimiterSession(
                per_minute=config.API_CALLS_PER_MINUTE
            )
            self.users = users_table

            if not self.users.exists():
                self.users.create_table()
        except NoRegionError as e:
            print(
                "[FATAL] Region not specified. Try adding AWS_DEFAULT_REGION to your env vars.",
                e,
            )
            raise
        except ClientError as e:
            print(
                f"Could not connect to DynamoDB",
                e.response["Error"]["Code"],
                e.response["Error"]["Message"],
            )
            raise

    def fetch(self):
        self.current_fetch_status = self._reset_fetch_status()
        start = datetime.now()

        number_of_calls = random.randint(*config.USERS_CALLS_PER_FETCH)
        for i in range(number_of_calls):
            self.event_logger.info(
                event={
                    "message": f"Performing call {i + 1}/{number_of_calls}",
                }
            )

            data = self._get_data(config.USERS_ENDPOINT)

            self.current_fetch_status["users"] += len(data)

            # Store them
            self.users.add_elements(data)

        elapsed = datetime.now() - start
        self.current_fetch_status["duration"] = elapsed.total_seconds()

        self.event_logger.status(
            event={"message": json.dumps(self.current_fetch_status)}
        )

        return self.current_fetch_status

    def _get_data(self, endpoint):
        self.current_fetch_status["api_calls"] += 1

        try:
            response = self.limiter_session.get(
                endpoint, params={"size": random.randint(*config.USERS_PER_API_CALL)}
            )

            if response.status_code != 200:
                error_event = {
                    "message": f"Received {response.status_code} code, but expected 200",
                    "response": response,
                }

                self.current_fetch_status["errors"].append(error_event)
                self.event_logger.error(error_event)

                return []

            data = response.json()
            # HEADS UP! Since the mock API always succeeds, we assume this as a failure.
            if "message" in data and data["message"] == "Maximum allowed size is 100":
                error_event = {
                    "message": "An unexpected error occurred when fetching users.",
                    "response": response,
                }

                self.current_fetch_status["errors"].append(error_event)
                self.event_logger.error(error_event)

                return []

            self.event_logger.info(
                event={
                    "message": f"Fetched {len(data)} users successfully.",
                }
            )

            return data
        except Exception as e:
            error_event = {
                "message": f"An unexpected Runtime error occurred. Exception: {e}",
            }
            self.event_logger.error(error_event)
            return []

    @staticmethod
    def _reset_fetch_status():
        return {
            "users": 0,
            "api_calls": 0,
            "errors": [],
            "timestamp": utils.get_timestamp(),
            "duration": 0,
        }

    def status(self):
        return self.event_logger.peek_status()

    def get(self):
        try:
            return self.users.get_elements()
        except Exception as e:
            print("[FAILURE] Something went wrong", e)
            return []
