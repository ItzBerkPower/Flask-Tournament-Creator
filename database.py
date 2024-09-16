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
        session['profile_id'] = existing_profile['profile_id'] # Make sure profile_id is in session
        return redirect(url_for('profile'))

    # Create a new profile
    cursor.execute('INSERT INTO player_profile (user_id, game) VALUES (?, ?)', (user_id, 'Fortnite'))
    conn.commit()

    profile_id = cursor.lastrowid
    session['profile_id'] = profile_id # Set profile_id in session

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
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM tournament')
        tournaments = cursor.fetchall()
    
    return render_template('tournaments.html', tournaments=tournaments)


@app.route('/create_team', methods=['GET', 'POST'])
def create_team():
    if not session.get('username'):
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))
    
    if not session.get('profile_id'):
        flash('You need to create a profile first.', 'warning')
        return redirect(url_for('profile'))
    
    if request.method == 'POST':
        team_name = request.form['team_name']

        if not team_name:
            flash('Team name cannot be empty!', 'danger')
            return redirect(url_for('team'))
    
        # Try finding the team
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM team WHERE team_name = ?', (team_name,))
            existing_team = cursor.fetchone()

            if existing_team:
                flash('Team name already exists. Please choose another name.', 'danger')
            
            else:
                cursor.execute('INSERT INTO team (team_name) VALUES (?)', (team_name,))
                conn.commit()
                flash(f'Team "{team_name}" created successfully!', 'success')

        return redirect(url_for('team'))

    return render_template('create_team.html')


@app.route('/join_team', methods=['GET', 'POST'])
def join_team():
    if not session.get('username'):
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))
    
    if not session.get('profile_id'):
        flash('You need to create a profile first.', 'warning')
        return redirect(url_for('profile'))
    
    if request.method == 'POST':
        team_name = request.form['team_name']

        with get_db() as conn:
            cursor = conn.cursor()

            cursor.execute('SELECT * FROM team WHERE team_name = ?', (team_name,))
            team = cursor.fetchone()

            if not team:
                flash('Team not found. Please check the team name or create a new one.', 'danger')

            else:
                team_id = team['team_id']
                profile_id = session['profile_id']

                cursor.execute('SELECT * FROM team_member WHERE team_id = ? AND profile_id = ?', (team_id, profile_id))
                existing_member = cursor.fetchone()

                if existing_member:
                    flash(f'You are already a member of the team "{team_name}".', 'info')

                else:
                    cursor.execute('INSERT INTO team_member (team_id, profile_id) VALUES (?, ?)', (team_id, profile_id))
                    conn.commit()
                    flash(f'You have successfully joined the team "{team_name}".', 'success')

    return render_template('join_team.html')




@app.route('/team')
def team():
    if not session.get('username'):
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))

    if not session.get('profile_id'):
        flash('You need to create a profile first.', 'warning')
        return redirect(url_for('profile'))


    with get_db() as conn:
        cursor = conn.cursor()
        profile_id = session['profile_id']

        # Check if the current player is already on a team
        cursor.execute('''
            SELECT team.team_id, team.team_name 
            FROM team_member 
            JOIN team ON team_member.team_id = team.team_id 
            WHERE team_member.profile_id = ?
        ''', (profile_id,))

        team_info = cursor.fetchone()

        if team_info:
            # If the player is on a team, get the usernames of all members on that team
            team_id = team_info['team_id']
            team_name = team_info['team_name']

            cursor.execute('''
                SELECT user.username 
                FROM team_member 
                JOIN player_profile ON team_member.profile_id = player_profile.profile_id
                JOIN user ON player_profile.user_id = user.user_id
                WHERE team_member.team_id = ?
            ''', (team_id,))
            team_members = cursor.fetchall()

            return render_template('team_info.html', team_name=team_name, team_members=team_members)

    # If the player is not on any team, show the create/join team options
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


@app.route('/create_tournament', methods=['GET', 'POST'])
def create_tournament():
    if not session.get('username'):
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))
    
    if not session.get('profile_id'):
        flash('You need to create a profile first.', 'warning')
        return redirect(url_for('profile'))

    if request.method == 'POST':
        tournament_name = request.form['tournament_name']
        game = request.form['game']
        start_date = request.form['start_date']
        end_date = request.form.get('end_date')  # Optional

        # Validate inputs
        if not tournament_name or not game or not start_date:
            flash('Tournament name, game, and start date are required!', 'danger')
            return redirect(url_for('create_tournament'))

        # Insert the tournament into the database
        with get_db() as conn:
            cursor = conn.cursor()
            
            # If end_date is provided, include it in the SQL query, otherwise omit it.
            if end_date:
                cursor.execute('''
                    INSERT INTO tournament (name, game, start_date, end_date)
                    VALUES (?, ?, ?, ?)
                    ''', (tournament_name, game, start_date, end_date))
            else:
                cursor.execute('''
                    INSERT INTO tournament (name, game, start_date)
                    VALUES (?, ?, ?)
                    ''', (tournament_name, game, start_date))
                
            conn.commit()
            flash(f'Tournament "{tournament_name}" created successfully!', 'success')
            return redirect(url_for('tournaments'))
        
    return render_template('create_tournament.html')


if __name__ == '__main__':  # Check if the script is run directly (not imported)
    init_db() # Initialise database
    app.run(debug=True)  # Run the Flask application with debug mode enabled


