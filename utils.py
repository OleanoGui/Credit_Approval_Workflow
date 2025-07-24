def get_email_template(status: str, credit_request_id: int, reason: str = None) -> dict:
    if status == "approved":
        subject = f"Credit Request #{credit_request_id} Approved"
        body = (
            f"Hello,\n\n"
            f"Your credit request #{credit_request_id} has been approved.\n"
            f"Congratulations! You will receive further instructions soon.\n\n"
            f"Best regards,\nCredit Approval Team"
        )
    elif status == "rejected":
        subject = f"Credit Request #{credit_request_id} Rejected"
        body = (
            f"Hello,\n\n"
            f"Your credit request #{credit_request_id} has been rejected.\n"
            f"Reason: {reason}\n\n"
            f"If you have questions, please contact support.\n\n"
            f"Best regards,\nCredit Approval Team"
        )
    elif status == "pending":
        subject = f"Credit Request #{credit_request_id} In Approval"
        body = (
            f"Hello,\n\n"
            f"Your credit request #{credit_request_id} is currently under review.\n"
            f"We will notify you once a decision is made.\n\n"
            f"Best regards,\nCredit Approval Team"
        )
    else:
        subject = "Credit Request Update"
        body = (
            f"Hello,\n\n"
            f"Your credit request #{credit_request_id} has a new status: {status}.\n\n"
            f"Best regards,\nCredit Approval Team"
        )
    return {"subject": subject, "body": body}