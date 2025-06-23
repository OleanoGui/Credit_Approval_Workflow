from tasks import process_credit_request

def test_process_credit_request():
    result = process_credit_request.run(123)
    assert result == {"request_id": 123, "status": "processed"}