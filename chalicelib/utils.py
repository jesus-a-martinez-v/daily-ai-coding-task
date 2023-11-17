from datetime import datetime
from datetime import timezone


def get_timestamp():
    # Current time in UTC
    return int(datetime.now(timezone.utc).timestamp() * 1000)
