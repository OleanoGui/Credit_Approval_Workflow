import unittest
from utils import get_email_template

class TestGetEmailTemplate(unittest.TestCase):
    def test_approved_template(self):
        result = get_email_template("approved", 123)
        self.assertIn("approved", result["subject"].lower())
        self.assertIn("approved", result["body"].lower())
        self.assertIn("123", result["subject"])
        self.assertIn("123", result["body"])

    def test_rejected_template(self):
        result = get_email_template("rejected", 456, reason="Low score")
        self.assertIn("rejected", result["subject"].lower())
        self.assertIn("rejected", result["body"].lower())
        self.assertIn("456", result["subject"])
        self.assertIn("456", result["body"])
        self.assertIn("Low score", result["body"])

    def test_pending_template(self):
        result = get_email_template("pending", 789)
        self.assertIn("in approval", result["subject"].lower())
        self.assertIn("under review", result["body"].lower())
        self.assertIn("789", result["subject"])
        self.assertIn("789", result["body"])

    def test_default_template(self):
        result = get_email_template("custom", 101)
        self.assertIn("update", result["subject"].lower())
        self.assertIn("custom", result["body"].lower())
        self.assertIn("101", result["subject"])
        self.assertIn("101", result["body"])

if __name__ == "__main__":
    unittest.main()