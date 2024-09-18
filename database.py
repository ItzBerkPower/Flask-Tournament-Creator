# ADD REGISTRATION DETECTION FOR UNIQUE ACCOUNTS  


from flask import Flask, render_template , request, redirect, url_for, flash, session # Import Flask and render_template for handling requests and rendering HTML templates
import os # Import os module to handle file paths
from sqlite3 import IntegrityError # Import sqlite3 for database handling
from werkzeug.security import generate_password_hash, check_password_hash # For passwords
from models import init_db, get_db # All the models for databse
from datetime import datetime

from flask_wtf import FlaskForm
from wtforms import StringField, EmailField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo

app = Flask(__name__)  # Initialize the Flask application

# Set a secret key for session management (required for using session)
app.secret_key = 'berkay'  # Replace 'your_secret_key' with a random string


class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password', message='Passwords must match')])
    submit = SubmitField('Register')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data
        password_hash = generate_password_hash(password)

        conn = get_db()
        cursor = conn.cursor()

        try:
            # Insert into the database
            cursor.execute('INSERT INTO user (username, email, password_hash) VALUES (?, ?, ?)', 
                           (username, email, password_hash))
            conn.commit()
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('index'))


        except IntegrityError:
            # Handle duplicate username or email
            flash('An account with that username or email already exists.', 'danger')
            conn.rollback()

        finally:
            conn.close()

    return render_template('register.html', form=form)


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
        session['profile_id'] = player_profile['profile_id']
    
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

    if not session.get('profile_id'):
        flash('You need to create a profile first.', 'warning')
        return redirect(url_for('profile'))
    
    profile_id = session.get('profile_id')
    tournament_info = None
    teams_in_tournament = []


    # Fetch all tournaments from the database
    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM tournament')
        tournaments = cursor.fetchall()

        # Check if the user is in a tournament
        cursor.execute('''
            SELECT tournament.name, tournament.tournament_id FROM tournament
            JOIN tournament_participant ON tournament.tournament_id = tournament_participant.tournament_id
            WHERE tournament_participant.profile_id = ?
        ''', (profile_id,))
        joined_tournament = cursor.fetchone()

        # Fetch all teams in the joined tournament (if any)
        teams_in_tournament = []
        if joined_tournament:
            cursor.execute('''
                SELECT team.team_name FROM team
                JOIN tournament_participant ON team.team_id = tournament_participant.team_id
                WHERE tournament_participant.tournament_id = ?
            ''', (joined_tournament['tournament_id'],))
            teams_in_tournament = cursor.fetchall()
            print(teams_in_tournament)

    return render_template('tournaments.html',
        tournaments=tournaments,
        joined_tournament=joined_tournament,
        teams_in_tournament=teams_in_tournament
    )


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



@app.route('/join_tournament/<int:tournament_id>', methods=['POST'])
def join_tournament(tournament_id):
    if not session.get('username'):
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))

    if not session.get('profile_id'):
        flash('You need to create a profile first.', 'warning')
        return redirect(url_for('profile'))

    profile_id = session.get('profile_id')

    # Check if the player is part of a team
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT team_id FROM team_member WHERE profile_id = ?
        ''', (profile_id,))
        team = cursor.fetchone()

        if not team:
            flash('You need to be part of a team to join a tournament.', 'danger')
            return redirect(url_for('tournaments'))

        team_id = team['team_id']

        # Check if the team has already joined the tournament
        cursor.execute('''
            SELECT * FROM tournament_participant WHERE tournament_id = ? AND team_id = ?
        ''', (tournament_id, team_id))
        existing_participant = cursor.fetchone()

        if existing_participant:
            flash('Your team has already joined this tournament.', 'info')
        else:
            # Join the tournament
            cursor.execute('''
                INSERT INTO tournament_participant (tournament_id, team_id, profile_id) VALUES (?, ?, ?)
            ''', (tournament_id, team_id, profile_id))
            conn.commit()
            flash('Your team has successfully joined the tournament!', 'success')

    return redirect(url_for('tournaments'))


@app.route('/logout')
def logout():
    # Clear the session to log out the user
    session.clear()
    flash('You have successfully logged out.', 'success')
    return redirect(url_for('index'))




# Updating stuff:

@app.route('/update_username', methods=['POST'])
def update_username():
    if not session.get('username'):
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))

    new_username = request.form.get('username')
    user_id = session['user_id']

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('UPDATE user SET username = ? WHERE user_id = ?', (new_username, user_id))
    conn.commit()
    session['username'] = new_username  # Update session with new username
    flash('Username updated successfully.', 'success')
    conn.close()

    return redirect(url_for('profile'))


@app.route('/update_email', methods=['POST'])
def update_email():
    if not session.get('username'):
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))

    new_email = request.form.get('email')
    user_id = session['user_id']

    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('UPDATE user SET email = ? WHERE user_id = ?', (new_email, user_id))
    conn.commit()
    flash('Email updated successfully.', 'success')
    conn.close()

    return redirect(url_for('profile'))


@app.route('/update_password', methods=['POST'])
def update_password():
    if not session.get('username'):
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))

    old_password = request.form.get('old_password')
    new_password = request.form.get('new_password')
    user_id = session['user_id']

    conn = get_db()
    cursor = conn.cursor()

    # Get the current password hash for the user
    cursor.execute('SELECT password_hash FROM user WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()

    if not user or not check_password_hash(user['password_hash'], old_password):
        flash('Incorrect current password.', 'danger')
    else:
        new_password_hash = generate_password_hash(new_password)
        cursor.execute('UPDATE user SET password_hash = ? WHERE user_id = ?', (new_password_hash, user_id))
        conn.commit()
        flash('Password updated successfully.', 'success')

    conn.close()
    return redirect(url_for('profile'))


# Route to render the main Quick Duel page
@app.route('/quick_duel')
def quick_duel():
    if not session.get('username'):
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))

    profile_id = session.get('profile_id')
    team_id = None
    duel_id = None
    match_data = None
    team1_name = team2_name = None

    with get_db() as conn:
        cursor = conn.cursor()

        # Check if the player is part of a team
        cursor.execute('''
            SELECT team_member.team_id
            FROM team_member
            WHERE team_member.profile_id = ?
        ''', (profile_id,))
        result = cursor.fetchone()

        if result:
            team_id = result['team_id']
        else:
            flash('You need to be part of a team to create or join a duel.', 'warning')
            return redirect(url_for('profile'))

        # Check if the team is already in a duel
        cursor.execute('''
            SELECT match.match_id, match.team1_id, match.team2_id, 
                   team1.team_name AS team1_name, team2.team_name AS team2_name
            FROM match
            LEFT JOIN team AS team1 ON match.team1_id = team1.team_id
            LEFT JOIN team AS team2 ON match.team2_id = team2.team_id
            WHERE match.team1_id = ? OR match.team2_id = ?
        ''', (team_id, team_id))
        match_data = cursor.fetchone()

        if match_data:
            duel_id = match_data['match_id']
            team1_name = match_data['team1_name']
            team2_name = match_data['team2_name']

    return render_template('quick_duel.html', duel_id=duel_id, team1_name=team1_name, team2_name=team2_name)

# Route to create a quick duel
@app.route('/create_duel', methods=['POST'])
def create_duel():
    if not session.get('username'):
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))

    profile_id = session.get('profile_id')
    team_id = None

    with get_db() as conn:
        cursor = conn.cursor()

        # Check if the player is part of a team
        cursor.execute('''
            SELECT team_member.team_id
            FROM team_member
            WHERE team_member.profile_id = ?
        ''', (profile_id,))
        result = cursor.fetchone()

        if result:
            team_id = result['team_id']
        else:
            flash('You need to be part of a team to create a duel.', 'warning')
            return redirect(url_for('profile'))

        # Create a new duel (match) and assign this user's team as team 1
        cursor.execute('''
            INSERT INTO match (team1_id, round)
            VALUES (?, 0)
        ''', (team_id,))
        conn.commit()
        flash('Quick duel created. You are Team 1.', 'success')

    return redirect(url_for('quick_duel'))


# Route to join an existing quick duel
@app.route('/join_duel', methods=['POST'])
def join_duel():
    if not session.get('username'):
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))

    profile_id = session.get('profile_id')
    team_id = None
    duel_id = request.form.get('duel_id')

    if not duel_id:
        flash('Please provide a duel ID to join.', 'danger')
        return redirect(url_for('quick_duel'))

    with get_db() as conn:
        cursor = conn.cursor()

        # Check if the player is part of a team
        cursor.execute('''
            SELECT team_member.team_id
            FROM team_member
            WHERE team_member.profile_id = ?
        ''', (profile_id,))
        result = cursor.fetchone()

        if result:
            team_id = result['team_id']
        else:
            flash('You need to be part of a team to join a duel.', 'warning')
            return redirect(url_for('profile'))

        # Check if the duel exists and if team 2 is empty
        cursor.execute('''
            SELECT match_id, team2_id
            FROM match
            WHERE match_id = ? AND team2_id IS NULL
        ''', (duel_id,))
        match_data = cursor.fetchone()

        if match_data:
            # Assign the user's team as team 2
            cursor.execute('''
                UPDATE match
                SET team2_id = ?
                WHERE match_id = ?
            ''', (team_id, duel_id))
            conn.commit()
            flash(f'You have joined Duel {duel_id} as Team 2.', 'success')
        else:
            flash('Invalid duel ID or duel already has two teams.', 'danger')

    return redirect(url_for('quick_duel'))

# Route to leave a duel
@app.route('/delete_duel', methods=['POST'])
def delete_duel():
    if not session.get('username'):
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))

    profile_id = session.get('profile_id')
    duel_id = request.form.get('duel_id')
    team_id = None

    with get_db() as conn:
        cursor = conn.cursor()

        # Check if the player is part of a team
        cursor.execute('''
            SELECT team_member.team_id
            FROM team_member
            WHERE team_member.profile_id = ?
        ''', (profile_id,))
        result = cursor.fetchone()

        if result:
            team_id = result['team_id']
        else:
            flash('You need to be part of a team to delete a duel.', 'warning')
            return redirect(url_for('profile'))

        # Remove the user's team from the duel
        cursor.execute('''
            DELETE FROM match WHERE (team1_id = ? OR team2_id = ?) AND match_id = ?
        ''', (team_id, team_id, duel_id))
        conn.commit()

        flash(f'You have deleted Duel {duel_id}.', 'success')

    return redirect(url_for('quick_duel'))








if __name__ == '__main__':  # Check if the script is run directly (not imported)
    init_db() # Initialise database
    app.run(debug=True)  # Run the Flask application with debug mode enabled


