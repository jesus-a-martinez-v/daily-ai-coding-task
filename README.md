# Overview
This application fetches User data from the [Random Data API site](https://random-data-api.com).

It stores the fetched data in a **DynamoDB** table keyed by ID and sorted by last name.

It also stores logs in CloudWatch, in three streams:
* **Info**: General information about the several operations performed by the system to fulfill its purpose.
* **Error**: Information about the errors that occasionally happen.
* **Status**: Keeps track of certain statistics about each fetch run, such as the number of users retrieved, timestamp, elapsed time, number of API requests performed and errors.

It uses a Dead Letter Queue to store information on **SQS** about the failed API calls to the Random Data API endpoint.

It uses **AWS Chalice** to implement the API, deploy it as a **Lambda** and expose it using **API Gateway**.

It uses GitHub Actions as the CI/CD solution.

Keep reading to learn more about this system!

## Installation

Running the project is very easy. Just follow the steps below and you'll be good to go! 👍🏼

## 1. Create conda environment
Run the following command to create the environment:

```shell
conda env create -f env.yml

# Activate it
source activate daily-ai-coding-task
```

## 2. Install the dependencies
```shell
pip install -r requirements.txt
```

## 3. Setup env vars
You'll need the following environment variables in your system
```shell
export AWS_ACCESS_KEY_ID=<id value>
export AWS_SECRET_ACCESS_KEY=<access key>
export AWS_DEFAULT_REGION=us-east-1
```

You can also create an `.env` file in the root of this project:

```text
AWS_ACCESS_KEY_ID=<id value>
AWS_SECRET_ACCESS_KEY=<access key>
AWS_DEFAULT_REGION=us-east-1
```

## 4. Deploy the app
If you already deployed this AWS Chalice project before, run:
```shell
chalice delete
```

If not, skip the previous step. Now, to deploy, run:

```shell
chalice deploy
```

After a few seconds, you should see the URL where the API is deployed, like this:

```text
Creating deployment package.
Creating IAM role: daily-ai-coding-task-dev-api_handler
Creating lambda function: daily-ai-coding-task-dev
Creating Rest API
Resources deployed:
  - Lambda ARN: arn:aws:lambda:us-east-1:365784738716:function:daily-ai-coding-task-dev
  - Rest API URL: https://ggmzoc406h.execute-api.us-east-1.amazonaws.com/api/

```

#### NOTE:
You can also test the app locally by running the following command:
```
chalice delete && chalice local
```

It'll be available on `localhost:8000`

---

## API

This application has three API endpoints, documented as follows:

### Endpoint: /status
It's used to retrieve information about the last fetch of data from a remote API.

If there is no information available, it will return `null`.

Example:
```
GET https://ggmzoc406h.execute-api.us-east-1.amazonaws.com/api/status
```

Response: 
```null```

Otherwise, it'll return information about the last fetch in JSON format:
Example: 
```
GET https://ggmzoc406h.execute-api.us-east-1.amazonaws.com/api/status
```

Response:
```json
{
    "users": 1623,
    "api_calls": 60,
    "errors": [
        {
            "host": "https://random-data-api.com/api/v2/users",
            "message": "An unexpected error occurred when fetching users.",
            "response": 200,
            "response_content": "{\"message\":\"Maximum allowed size is 100\"}"
        },
        {
            "host": "https://random-data-api.com/api/v2/users",
            "message": "An unexpected error occurred when fetching users.",
            "response": 200,
            "response_content": "{\"message\":\"Maximum allowed size is 100\"}"
        },
        {
            "host": "https://random-data-api.com/api/v2/users",
            "message": "An unexpected error occurred when fetching users.",
            "response": 200,
            "response_content": "{\"message\":\"Maximum allowed size is 100\"}"
        },
        {
            "host": "https://random-data-api.com/api/v2/users",
            "message": "An unexpected error occurred when fetching users.",
            "response": 200,
            "response_content": "{\"message\":\"Maximum allowed size is 100\"}"
        },
        {
            "host": "https://random-data-api.com/api/v2/users",
            "message": "An unexpected error occurred when fetching users.",
            "response": 200,
            "response_content": "{\"message\":\"Maximum allowed size is 100\"}"
        },
        {
            "host": "https://random-data-api.com/api/v2/users",
            "message": "An unexpected error occurred when fetching users.",
            "response": 200,
            "response_content": "{\"message\":\"Maximum allowed size is 100\"}"
        },
        {
            "host": "https://random-data-api.com/api/v2/users",
            "message": "An unexpected error occurred when fetching users.",
            "response": 200,
            "response_content": "{\"message\":\"Maximum allowed size is 100\"}"
        },
        {
            "host": "https://random-data-api.com/api/v2/users",
            "message": "An unexpected error occurred when fetching users.",
            "response": 200,
            "response_content": "{\"message\":\"Maximum allowed size is 100\"}"
        },
        {
            "host": "https://random-data-api.com/api/v2/users",
            "message": "An unexpected error occurred when fetching users.",
            "response": 200,
            "response_content": "{\"message\":\"Maximum allowed size is 100\"}"
        },
        {
            "host": "https://random-data-api.com/api/v2/users",
            "message": "An unexpected error occurred when fetching users.",
            "response": 200,
            "response_content": "{\"message\":\"Maximum allowed size is 100\"}"
        },
        {
            "host": "https://random-data-api.com/api/v2/users",
            "message": "An unexpected error occurred when fetching users.",
            "response": 200,
            "response_content": "{\"message\":\"Maximum allowed size is 100\"}"
        },
        {
            "host": "https://random-data-api.com/api/v2/users",
            "message": "An unexpected error occurred when fetching users.",
            "response": 200,
            "response_content": "{\"message\":\"Maximum allowed size is 100\"}"
        },
        {
            "host": "https://random-data-api.com/api/v2/users",
            "message": "An unexpected error occurred when fetching users.",
            "response": 200,
            "response_content": "{\"message\":\"Maximum allowed size is 100\"}"
        },
        {
            "host": "https://random-data-api.com/api/v2/users",
            "message": "An unexpected error occurred when fetching users.",
            "response": 200,
            "response_content": "{\"message\":\"Maximum allowed size is 100\"}"
        },
        {
            "host": "https://random-data-api.com/api/v2/users",
            "message": "An unexpected error occurred when fetching users.",
            "response": 200,
            "response_content": "{\"message\":\"Maximum allowed size is 100\"}"
        },
        {
            "host": "https://random-data-api.com/api/v2/users",
            "message": "An unexpected error occurred when fetching users.",
            "response": 200,
            "response_content": "{\"message\":\"Maximum allowed size is 100\"}"
        },
        {
            "host": "https://random-data-api.com/api/v2/users",
            "message": "An unexpected error occurred when fetching users.",
            "response": 200,
            "response_content": "{\"message\":\"Maximum allowed size is 100\"}"
        },
        {
            "host": "https://random-data-api.com/api/v2/users",
            "message": "An unexpected error occurred when fetching users.",
            "response": 200,
            "response_content": "{\"message\":\"Maximum allowed size is 100\"}"
        },
        {
            "host": "https://random-data-api.com/api/v2/users",
            "message": "An unexpected error occurred when fetching users.",
            "response": 200,
            "response_content": "{\"message\":\"Maximum allowed size is 100\"}"
        },
        {
            "host": "https://random-data-api.com/api/v2/users",
            "message": "An unexpected error occurred when fetching users.",
            "response": 200,
            "response_content": "{\"message\":\"Maximum allowed size is 100\"}"
        },
        {
            "host": "https://random-data-api.com/api/v2/users",
            "message": "An unexpected error occurred when fetching users.",
            "response": 200,
            "response_content": "{\"message\":\"Maximum allowed size is 100\"}"
        },
        {
            "host": "https://random-data-api.com/api/v2/users",
            "message": "An unexpected error occurred when fetching users.",
            "response": 200,
            "response_content": "{\"message\":\"Maximum allowed size is 100\"}"
        },
        {
            "host": "https://random-data-api.com/api/v2/users",
            "message": "An unexpected error occurred when fetching users.",
            "response": 200,
            "response_content": "{\"message\":\"Maximum allowed size is 100\"}"
        },
        {
            "host": "https://random-data-api.com/api/v2/users",
            "message": "An unexpected error occurred when fetching users.",
            "response": 200,
            "response_content": "{\"message\":\"Maximum allowed size is 100\"}"
        },
        {
            "host": "https://random-data-api.com/api/v2/users",
            "message": "An unexpected error occurred when fetching users.",
            "response": 200,
            "response_content": "{\"message\":\"Maximum allowed size is 100\"}"
        }
    ],
    "timestamp": 1700449327942,
    "duration": 24.515415
}
```

### Endpoint: /view-data
Retrieves all the data stored about users.

Example:
```
GET https://ggmzoc406h.execute-api.us-east-1.amazonaws.com/api/view-data
```

Response:
```json
[
    {
        "employment": {
            "title": "Future Technician",
            "key_skill": "Work under pressure"
        },
        "avatar": "https://robohash.org/quasinostrumiste.png?size=300x300&set=set1",
        "credit_card": {
            "cc_number": "4396-8073-7993-3981"
        },
        "subscription": {
            "term": "Payment in advance",
            "plan": "Basic",
            "payment_method": "Visa checkout",
            "status": "Pending"
        },
        "social_insurance_number": "457510386",
        "address": {
            "street_address": "1043 Miller Street",
            "country": "United States",
            "city": "Matildamouth",
            "coordinates": {
                "lng": 14.327821264956924,
                "lat": 32.6874879236812
            },
            "state": "Iowa",
            "street_name": "Gerhold Glens",
            "zip_code": "09914"
        },
        "date_of_birth": "1969-05-08",
        "email": "yolando.howell@email.com",
        "uid": "7547a6ab-623d-4ca9-b31f-67f1e518bdf7",
        "gender": "Genderfluid",
        "password": "pDw6jSZcYW",
        "last_name": "Howell",
        "first_name": "Yolando",
        "phone_number": "+221 1-668-067-7459 x63595",
        "username": "yolando.howell",
        "id": 6207.0
    },
    {
        "employment": {
            "title": "Manufacturing Architect",
            "key_skill": "Technical savvy"
        },
        "avatar": "https://robohash.org/quiofficiisexpedita.png?size=300x300&set=set1",
        "credit_card": {
            "cc_number": "4700-2371-5573-3846"
        },
        "subscription": {
            "term": "Annual",
            "plan": "Gold",
            "payment_method": "Money transfer",
            "status": "Blocked"
        },
        "social_insurance_number": "784737652",
        "address": {
            "street_address": "241 Marlana Walk",
            "country": "United States",
            "city": "East Joellachester",
            "coordinates": {
                "lng": -122.88197527126397,
                "lat": 81.76133237287092
            },
            "state": "New Jersey",
            "street_name": "Crooks Points",
            "zip_code": "88429"
        },
        "date_of_birth": "1979-08-24",
        "email": "andrew.metz@email.com",
        "uid": "96475721-85c2-4893-ba8d-dfb5a4b9f2ac",
        "gender": "Female",
        "password": "gsM7PhFIbq",
        "last_name": "Metz",
        "first_name": "Andrew",
        "phone_number": "+234 122-158-3395",
        "username": "andrew.metz",
        "id": 1091.0
    },
    ...    
]
```

## Improvements:
* Better handling of DLQ (right now, we are manually sending messages, but could use SQS's buil-in DLQ support).
* Refactor tests to avoid so much repeated code.
* Make the data fetch async.
* Optimize queries from Dynamo instead of scanning.
* Use IAM/API Keys to handle access to the API.
* Sometimes Dynamo throws a ProvisionedThroughputExceededException when batch writing, but this is expected since the provisioned throughput was set to 1 to keep running costs as low as possible.