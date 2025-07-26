import unittest
from unittest.mock import patch, MagicMock
import notifications

class DummyUser:
    def __init__(self, email=None, phone=None, notify_email=True, notify_sms=False):
        self.email = email
        self.phone = phone
        self.notify_email = notify_email
        self.notify_sms = notify_sms

class TestNotifications(unittest.TestCase):
    @patch("notifications.smtplib.SMTP")
    def test_send_email(self, mock_smtp):
        notifications.send_email("to@example.com", "Subject", "Body", from_email="from@example.com")
        mock_smtp.assert_called_once()
        instance = mock_smtp.return_value.__enter__.return_value
        instance.starttls.assert_called_once()
        instance.login.assert_called_once()
        instance.sendmail.assert_called_once()

    @patch("notifications.print")
    def test_send_sms(self, mock_print):
        notifications.send_sms("+5511999999999", "Test message")
        mock_print.assert_called_with("SMS to +5511999999999: Test message")

    @patch("notifications.send_email")
    @patch("notifications.send_sms")
    def test_send_notification(self, mock_send_sms, mock_send_email):
        user = DummyUser(email="user@example.com", phone="+5511999999999", notify_email=True, notify_sms=True)
        notifications.send_notification(user, "Subject", "Message")
        mock_send_email.assert_called_once_with("user@example.com", "Subject", "Message")
        mock_send_sms.assert_called_once_with("+5511999999999", "Message")

    @patch("notifications.send_email")
    @patch("notifications.send_sms")
    def test_send_notification_only_email(self, mock_send_sms, mock_send_email):
        user = DummyUser(email="user@example.com", notify_email=True, notify_sms=False)
        notifications.send_notification(user, "Subject", "Message")
        mock_send_email.assert_called_once_with("user@example.com", "Subject", "Message")
        mock_send_sms.assert_not_called()

    @patch("notifications.send_email")
    @patch("notifications.send_sms")
    def test_send_notification_only_sms(self, mock_send_sms, mock_send_email):
        user = DummyUser(phone="+5511999999999", notify_email=False, notify_sms=True)
        notifications.send_notification(user, "Subject", "Message")
        mock_send_email.assert_not_called()
        mock_send_sms.assert_called_once_with("+5511999999999", "Message")

if __name__ == "__main__":
    unittest.main()