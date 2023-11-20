from datetime import datetime
from datetime import timezone


def get_timestamp_millis():
    # Convert the current UTC time to a timestamp in milliseconds and return it.
    return int(datetime.now(timezone.utc).timestamp() * 1000)
