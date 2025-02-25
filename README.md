# Payment Processing API

This project is an asynchronous payment processing API built with FastAPI. It handles payment transactions in the background, integrates with external services (for loyalty and notifications), and uses separate databases for user balances and payment records.

## Features

- **Asynchronous Processing:** Uses FastAPI with background tasks for non-blocking operations.
- **Database Separation:** Maintains user (wallet) data and payment records in separate databases.
- **Reliable Transactions:** Implements custom retry logic and explicit transaction management.
- **External Service Integration:** Communicates with external APIs for loyalty rewards and notifications.
