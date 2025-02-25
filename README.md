# Payment Processing API

This project is an asynchronous payment processing API built with FastAPI. It handles payment transactions in the background, integrates with external services (for loyalty and notifications), and uses separate databases for user balances and payment records.

## Features

- **Asynchronous Processing:** Uses FastAPI with background tasks for non-blocking operations.
- **Database Separation:** Maintains user (wallet) data and payment records in separate databases.
- **Reliable Transactions:** Implements custom retry logic and explicit transaction management.
- **External Service Integration:** Communicates with external APIs for loyalty rewards and notifications.

## Database Initialization
Before starting the application, initialize the databases if they do not exist. The database initialization script is located at app/utils/db/init.py.

To run the initialization script, execute:
```sh
python -m app.utils.db.init
```

## Running the Application
To run the application using uvicorn:
```sh
uvicorn app.main:app --host $HOST --port $PORT --reload
```
Alternatively, you can run it via:
```sh
python -m app.main
```

## Running External Services
### Loyalty Service

```sh
python -m app.services.loyalty
```
or using uvicorn:

```sh
uvicorn app.services.loyalty:app --host 0.0.0.0 --port 8001 --reload
```
### Notification Service

```sh
python -m app.services.notification
```
or using uvicorn:

```sh
uvicorn app.services.notification:app --host 0.0.0.0 --port 8002 --reload
```

