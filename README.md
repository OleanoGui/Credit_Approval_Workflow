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

🔹 Key Features

- **API Versioning:** All endpoints are under `/api/v1/`
- **Advanced Filtering & Pagination:** Filter requests by status, user, date, amount, etc.
- **RBAC:** Role-based access control for admin, manager, analyst
- **Smart Caching:** Per-user and per-query parameter cache for performance
- **Audit Logging:** All important actions (approve, reject, create) are logged
- **Notifications:** Email notifications sent to users about request status
- **Backup & Restore:** Automated database backup routines
- **Observability:** Prometheus metrics exposed at `/metrics`, with alerting rules
- **Accessibility:** Frontend components follow accessibility best practices
- **Frontend Dashboard:** Metrics charts with filters and drill-down
- **CI/CD:** Automated pipelines for testing, linting, and deployment

🔹 Project Structure

📂 models.py      # Table definitions (User, CreditRequest, ApprovalStage, AuditLog)
📂 routes.py      # API endpoints (credit requests, approvals, authentication)
📂 tasks.py       # Asynchronous processing with Celery
📂 messaging.py   # Service communication (RabbitMQ/Kafka)
📂 auth.py        # Authentication and permission control
📂 utils.py       # Utility functions (email notifications, backup)
📂 tests/         # Unit and integration tests
📂 frontend/      # React frontend (Material UI, Axios)


🔹 Frontend

The frontend was developed in React, using Material UI for the interface and Axios for backend communication.

- **Login screen** with JWT authentication
- **User registration**
- **Create and track credit requests**
- **Status viewing and filtering**
- **Role-based screens and permissions**
- **Accessible forms and dashboards**
- **Metrics dashboard** with filters and drill-down charts

To run the frontend locally:
```bash
cd frontend
npm install
npm start
```

## 📊 Observability: Prometheus & Grafana

- Metrics exposed at `/metrics` via [prometheus_fastapi_instrumentator](https://github.com/trallard/prometheus-fastapi-instrumentator)
- Example queries:
  - `http_server_requests_total` — total HTTP requests by endpoint/method/status
  - `http_request_duration_seconds_count` — request duration count
- Alerting rules in `alert.rules.yml` (latency, CPU, memory, etc.)

🔒 Authentication & Security

- **Obtain token:**  
  `POST /api/v1/token` with username and password
- **Use token:**  
  Pass `Authorization: Bearer <token>` header for protected endpoints

**Example:**
```bash
# Get token
curl -X POST "http://localhost:8000/api/v1/token" -d "username=admin&password=yourpassword"

# Use token
curl -H "Authorization: Bearer <access_token>" "http://localhost:8000/api/v1/credit-requests/"
```

- **Refresh token:**  
  `POST /api/v1/refresh` with refresh token to obtain new access token
- **Logout:**  
  Secure logout with token blacklist

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

🛠️ CI/CD

- GitHub Actions pipeline runs tests, lint, and deploys on push/pull request
- Workflow file: `.github/workflows/ci.yml`


🧩 Extensibility

- Modular codebase for easy addition of new approval stages, notification channels, or integrations
- Ready for production deployment with Docker