from datetime import datetime
from datetime import timezone


def get_timestamp_millis():
    # Current time in UTC
    return int(datetime.now(timezone.utc).timestamp() * 1000)
