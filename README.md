📌 Project: Credit Approval Workflow
Description: A backend system that manages credit requests, going through different approval stages before final 
approval.

🔹 Technologies

Python – Main programming language
FastAPI – Framework for APIs
Celery + Redis – For asynchronous processing of approvals
RabbitMQ/Kafka – For service-to-service messaging
PostgreSQL – Database to store credit requests
OAuth2 + JWT – Authentication and access control
Docker – To simplify the development environment



🚀 Approval Workflow
1️⃣ Credit Request
The user submits a request with financial data
The request is placed in a processing queue

2️⃣ Automatic Analysis
The system checks credit score, income, and financial history
If approved, the request moves to human approval

3️⃣ Managerial Approval
The request goes through different levels of approval (e.g., analyst → manager → director)
Each approver receives a notification and can approve or reject

4️⃣ Final Decision
If all approval stages are completed, the credit is granted
The user is notified of the final status



🔹 Project Structure

📂 models.py → Table definitions (CreditRequest, User, ApprovalStage)
📂 routes.py → API routes to create requests and check status
📂 tasks.py → Asynchronous processing using Celery
📂 messaging.py → Communication between services using RabbitMQ/Kafka
📂 auth.py → User authentication and permission control

🔹 Frontend

The frontend was developed in React, using Material UI for the interface and Axios for backend communication.

Main features:
- Login screen with JWT authentication
- User registration
- Creation and tracking of credit requests
- Viewing the status of requests
- Different screens and permissions according to user role (admin, manager, user)

To run the frontend locally:
```bash
cd frontend
npm install
npm start
```

## 📊 Observability: Prometheus & Grafana

This project exposes application metrics at `/metrics` using [prometheus_fastapi_instrumentator](https://github.com/trallard/prometheus-fastapi-instrumentator).

## Example panel query

- `http_server_requests_total` — total HTTP requests by endpoint/method/status
- `http_request_duration_seconds_count` — request duration count

## 📊 Example Prometheus Metrics Displayed

- Total requests per endpoint/method/status (2xx, 4xx, 5xx)
- Request duration histograms

## Requirements

- Docker Desktop
- Python dependencies: `prometheus-fastapi-instrumentator`

## 🧪 Running Tests

This project includes unit tests for the main modules:

### Auth Tests (`tests/test_auth.py`)
- Password hashing and verification
- JWT access token creation
- User authentication (success and failure cases)

### Models Tests (`tests/test_models.py`)
- User creation and persistence
- Credit request creation and default status

### Routes Tests (`tests/test_routes.py`)
- (Add a brief description of your route tests here, for example:)
- Endpoint responses and status codes
- Authentication and authorization flows
- Business logic for credit request approval/rejection

### How to Run All Tests

From the project root, run:
```bash
pytest
```

All tests are located in the `tests/` directory and use an in-memory SQLite database for isolation and speed.