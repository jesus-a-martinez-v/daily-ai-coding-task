# The endpoint URL for the random user data API.
USERS_ENDPOINT = "https://random-data-api.com/api/v2/users"

# The number of API calls allowed per minute to avoid rate limiting.
API_CALLS_PER_MINUTE = 75

# The number of days to retain data in CloudWatch.
RETENTION_PERIOD_IN_DAYS = 30

# The name of the log group in CloudWatch
LOG_GROUP = "DailyAIDataFetcher"

# Log stream names for different types of logs within the log group.
ERROR_LOG_STREAM = "Error"  # Log stream for error messages.
STATUS_LOG_STREAM = "Status"  # Log stream for status updates.
INFO_LOG_STREAM = "Info"  # Log stream for informational messages.

# A tuple representing the minimum and maximum number of users to fetch per API call.
USERS_PER_API_CALL = (1, 150)

# A tuple indicating the range of number of calls to make for each data fetch operation.
USERS_CALLS_PER_FETCH = (1, 20)
