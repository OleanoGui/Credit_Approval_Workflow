from celery import Celery

celery_app = Celery(
    "tasks",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

@celery_app.task
def process_credit_request(credit_request_id):

    print(f"Processing credit request {credit_request_id}")

    return {"request_id": credit_request_id, "status": "processed"}