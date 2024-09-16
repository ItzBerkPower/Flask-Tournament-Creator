from flask import Flask, render_template , request, redirect, url_for, flash, session # Import Flask and render_template for handling requests and rendering HTML templates
import os # Import os module to handle file paths
import sqlite3 # Import sqlite3 for database handling
from werkzeug.security import generate_password_hash, check_password_hash # For passwords
from models import init_db, get_db # All the models for databse
from datetime import datetime

app = Flask(__name__)  # Initialize the Flask application

# Set a secret key for session management (required for using session)
app.secret_key = 'berkay'  # Replace 'your_secret_key' with a random string


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        password_hash = generate_password_hash(password)

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute('INSERT INTO user (username, email, password_hash) VALUES (?, ?, ?)', 
                        (username, email, password_hash))

        conn.commit()
        conn.close()
        
        return redirect(url_for('index'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        # Retrieve user from the database
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM user WHERE email = ?', (email,))
        user = cursor.fetchone()
        conn.close()
        
        if user and check_password_hash(user['password_hash'], password):
            # Correct credentials, log the user in
            session['user_id'] = user['user_id']
            session['username'] = user['username']

            return redirect(url_for('index'))
        
        else:
            # Invalid credentials
            flash('Invalid email or password. Please try again.', 'danger')
    
    return render_template('login.html')


@app.route('/')  # Define the route for the homepage
def index():
    return render_template('index.html')


# {website}/profile
@app.route('/profile')
def profile():
    if not session.get('username'):
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM player_profile WHERE user_id = ?', (user_id,))
    player_profile = cursor.fetchone()

    player_statistics = None
    if player_profile:
        # Fetch player's statistics if the profile exists
        cursor.execute('SELECT * FROM player_statistics WHERE profile_id = ?', (player_profile['profile_id'],))
        player_statistics = cursor.fetchone()
    
    conn.close()

    return render_template('profile.html', player_profile=player_profile, player_statistics=player_statistics)


@app.route('/create_profile', methods=['POST'])
def create_profile():
    if not session.get('username'):
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))

    user_id = session['user_id']

    # Check if the user already has a profile
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM player_profile WHERE user_id = ?', (user_id,))
    existing_profile = cursor.fetchone()

    if existing_profile:
        flash('Profile already exists.', 'info')
        return redirect(url_for('profile'))

    # Create a new profile
    cursor.execute('INSERT INTO player_profile (user_id, game) VALUES (?, ?)', (user_id, 'Fortnite'))
    conn.commit()

    profile_id = cursor.lastrowid

    # After committing the profile, create a PlayerStatistics record
    cursor.execute('INSERT INTO player_statistics (profile_id, total_kills, total_deaths, total_assists) VALUES (?, ?, ?, ?)',
                   (profile_id, 0, 0, 0))
    conn.commit()
    conn.close()

    flash('Profile created successfully!', 'success')
    return redirect(url_for('profile'))


@app.route('/tournaments')
def tournaments():
    if not session.get('username'):
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))
    
    # Fetch all tournaments from the database
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM tournament')
    tournaments = cursor.fetchall()

    print("Tournaments fetched:", tournaments)  # Debugging line

    conn.close()

    
    return render_template('tournaments.html', tournaments=tournaments)


@app.route('/team')
def team():
    if not session.get('username'):
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))
    
    return render_template('team.html')




# UPDATING PROFILE DETAILS
@app.route('/update_game', methods=['POST'])
def update_game():
    if not session.get('username'):
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))

    user_id = session['user_id']
    selected_game = request.form['game']

    # Find the player's profile and update the game
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE player_profile SET game = ? WHERE user_id = ?', (selected_game, user_id))
    conn.commit()
    conn.close()

    flash(f'Game updated to {selected_game}', 'success')
    return redirect(url_for('profile'))


if __name__ == '__main__':  # Check if the script is run directly (not imported)
    init_db() # Initialise database
    app.run(debug=True)  # Run the Flask application with debug mode enabled


