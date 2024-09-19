# ADD REGISTRATION DETECTION FOR UNIQUE ACCOUNTS  

# ALL IMPORTS 
from flask import render_template , request, redirect, url_for, flash, session # All Flask imports
from sqlite3 import IntegrityError # # Actual database handling
from werkzeug.security import generate_password_hash, check_password_hash # For passwords
from models import * # All model imports

# Form imports
from flask_wtf import FlaskForm
from wtforms import StringField, EmailField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo

# View imports
from tournament_views import *
from profile_views import *
from duel_views import *
from team_views import *


# Class for the registration form (Secure registration)
class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password', message='Passwords must match')])
    submit = SubmitField('Register')



# Route to register user
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm() # Call the class
    
    # When submit button pressed, gather all form data
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data
        password_hash = generate_password_hash(password)


        # Initialise the cursor
        conn = get_db()
        cursor = conn.cursor()

        try:
            # Try inserting user into database
            cursor.execute('INSERT INTO user (username, email, password_hash) VALUES (?, ?, ?)', 
                           (username, email, password_hash))
            conn.commit()
            flash('Registration successful! You can now log in.', 'success') # Successful, print success message
            return redirect(url_for('index')) # Send user back to home page


        # If error, where that username / email already exists, send warning message instead of crashing program
        except IntegrityError:
            flash('An account with that username or email already exists.', 'danger')
            conn.rollback()

        # Close the cursor object
        finally:
            conn.close()

    return render_template('register.html', form=form) # Render template





# Route for user to login (Uses basic form)
@app.route('/login', methods=['GET', 'POST'])
def login():

    # Gather email and password from form after submission
    if request.method == 'POST': 
        email = request.form['email']
        password = request.form['password']
        
        # Try to find user from database
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM user WHERE email = ?', (email,))
            user = cursor.fetchone()
        
        # If the user row is correct, and the password is correct, update the session to log user in
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['user_id']
            session['username'] = user['username']

            return redirect(url_for('index')) # Send user back to home page
        
        else:
            flash('Invalid email or password. Please try again.', 'danger') # Can't find user, send warning message
    
    return render_template('login.html') # Render template


# Route to log out user
@app.route('/logout')
def logout():
    session.clear() # Clear session to log out user
    flash('You have successfully logged out.', 'success') # Send success message
    return redirect(url_for('index')) # Send user back to home page


# Route for landing page
@app.route('/')
def index():
    return render_template('index.html') # Render the homepage template

# Check if script run directly (Not imported)
if __name__ == '__main__':
    init_db() # Initialise database
    app.run(debug=True)  # Run the Flask application with debug mode enabled
