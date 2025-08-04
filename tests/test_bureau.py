import unittest
from unittest.mock import patch, MagicMock
from bureau import cpf_bureau_check

class TestBureau(unittest.TestCase):
    @patch("bureau.requests.post")
    def test_cpf_bureau_check_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"restriction": False}
        mock_post.return_value = mock_response

        result = cpf_bureau_check("12345678900")
        self.assertEqual(result, {"restriction": False})

    @patch("bureau.requests.post")
    def test_cpf_bureau_check_error(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Invalid CPF"
        mock_post.return_value = mock_response

        result = cpf_bureau_check("invalid")
        self.assertEqual(result, {"error": "Invalid CPF"})

if __name__ == "__main__":
    unittest.main()