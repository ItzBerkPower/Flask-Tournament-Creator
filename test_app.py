import unittest
from app import app

class FlaskTestase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
    
    # Test for the home page route
    def test_home_page(self):
        result = self.app.get('/')  # Make a GET request to the '/' route
        self.assertEqual(result.status_code, 200)  # Assert that the status code is 200
        self.assertIn(b'Home', result.data)  # Check if 'Home' or some expected content is in the page

if __name__ == '__main__':
    unittest.main()