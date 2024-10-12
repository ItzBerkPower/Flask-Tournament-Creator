import unittest
from app import app
from flask import session

class FlaskTestase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True


    # Test for the home page route
    def test_home_page(self):
        result = self.app.get('/')  # Make a GET request to the '/' route
        self.assertEqual(result.status_code, 200)  # Assert that the status code is 200
        self.assertIn(b'Welcome', result.data)  # Check if 'Home' or some expected content is in the page


    # TESTING LOGIN FUNCTIONALITY (FORM SUBMISSIONS)

    # Test a successful login
    def test_successful_login(self):

        with self.app as unused: # To allow access to session

            # Simulate POST request to /login with correct email and password
            result = self.app.post('/login', data={
                'email': 'a@hotmail.com',
                'password': 'a'})  
                # (follow_redirects is to make sure the POST request follows the redirect back to the home page, as this means login was successful)

            self.assertEqual(result.status_code, 302) # Check if the status code is 302, as there is a redirect
            self.assertIn(b'Redirecting...', result.data)  # Check if some success message or content appears on the redirected page

            # Check if username is set in session
            self.assertIn('username', session) # Check if there is a username in the session
            self.assertEqual(session['username'], 'a') # Check if that username is this accounts' one


    # Test a failed login (Wrong credentials)
    def test_failed_login(self):

        with self.app as unused: # To allow access to session

            # Simulate POST request to /login with incorrect password or incorrect email
            result = self.app.post('/login', data={
                'email': 'wrongusername',
                'password': 'wrongpassword'}, follow_redirects=True)

            self.assertNotEqual(result.status_code, 302) # Check if the status code is not 302 (Since there shouldn't be a redirect)
            self.assertIn(b'Invalid email or password. Please try again.', result.data) # Check if the error message appears in the response data

            self.assertNotIn('username', session) # Check that the session does not contain the username after failed login   
    




    # TESTING IF A USER CAN ACCESS A PROTECTED PAGE (PAGE THEY CAN ONLY ACCESS WHEN LOGGED IN)

    # Accessing a protected page without logging in
    def protected_page_before_login(self):
        with self.app as unused:
            self.assertNotIn('username', session) # Check that there is no username in session (User hasn't logged in)

            result = self.app.get('/quick_duel', follow_redirects=True) # Access the duels page, which requires logging in
            self.assertEqual(result.status_code, 200) # This time follow the redirects, and check if a success 200 status code, to check that user has been redirected to login page
            self.assertIn(b'You need to log in first.', result.data)  # Ensure the error message is printed
    

    # Accessing a protected page after logging in
    def test_protected_page_after_login(self):
        self.app.post('/login', data=dict(email='a@hotmail.com', password='a'), follow_redirects=True) # Log in the user (Account already has profile)
        
        # Now try accessing the protected page
        result = self.app.get('/quick_duel', follow_redirects=True)
        self.assertEqual(result.status_code, 200)
        self.assertIn(b'Quick Duel', result.data)  # Ensure the user can access the duels page



    # ACCESSING A NON-EXISTENT WEBPAGE
    
    def non_existent_page(self):
        result = self.app.get('/duels') # Any non-existent page can be placed here, I placed duels because most common one
        self.assertEqual(result.status_code, 404)  # Expecting 'Page Not Found' error




if __name__ == '__main__':
    unittest.main()