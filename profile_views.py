# ALL IMPORTS
from flask import render_template , request, redirect, url_for, flash, session # Import Flask and render_template for handling requests and rendering HTML templates
from sqlite3 import IntegrityError # Import sqlite3 for database handling
from werkzeug.security import generate_password_hash, check_password_hash # For passwords
from models import * # All the models for databse
from datetime import datetime



# Route for profile page
@app.route('/profile')
def profile():

    #check_if_user_exists()
    # ------------------------------------------------------
    if not session.get('username'):
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))
    # ---------------------------------------------------------
    
    user_id = session['user_id']
    
    with get_db() as conn:
        cursor = conn.cursor() # Initialise cursor object

        cursor.execute('SELECT * FROM player_profile WHERE user_id = ?', (user_id,)) # Get the players user profile
        player_profile = cursor.fetchone()

        player_statistics = None
        # If profile exists, fetch player stats
        if player_profile:
            cursor.execute('SELECT * FROM player_statistics WHERE profile_id = ?', (player_profile['profile_id'],))
            player_statistics = cursor.fetchone()
            session['profile_id'] = player_profile['profile_id'] # Update the session
    

    return render_template('profile.html', player_profile=player_profile, player_statistics=player_statistics) # Render template


# Route to create actual profile (Is button)
@app.route('/create_profile', methods=['POST'])
def create_profile():
    
    #check_if_user_exists()
    # ------------------------------------------------------
    if not session.get('username'):
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))
    # ---------------------------------------------------------

    user_id = session['user_id'] # Get user id from session

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM player_profile WHERE user_id = ?', (user_id,)) # Check if user already has profile
        existing_profile = cursor.fetchone()

        # If user has profile, give warning message without crashing website
        if existing_profile:
            flash('Profile already exists.', 'info')
            session['profile_id'] = existing_profile['profile_id'] # Make sure profile_id is in session
            return redirect(url_for('profile')) # Reload page

        # If not, create a new profile
        cursor.execute('INSERT INTO player_profile (user_id, game) VALUES (?, ?)', (user_id, 'Fortnite'))
        conn.commit()

        profile_id = cursor.lastrowid
        session['profile_id'] = profile_id # Set profile_id in session

        # After committing the profile, create a PlayerStatistics record
        cursor.execute('INSERT INTO player_statistics (profile_id, total_kills, total_deaths, total_assists) VALUES (?, ?, ?, ?)',
                    (profile_id, 0, 0, 0))
        conn.commit()

    flash('Profile created successfully!', 'success') # Success message
    return redirect(url_for('profile')) # Reload the page





# UPDATING PROFILE DETAILS

# Update the game of the user (Dropdown menu)
@app.route('/update_game', methods=['POST'])
def update_game():
    
    #check_if_user_exists()
    # ---------------------------------------------
    if not session.get('username'):
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))
    # -----------------------------------------------
    
    # Get the user id from session and current game
    user_id = session['user_id']
    selected_game = request.form['game']

    # Find the player's profile and update their game
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('UPDATE player_profile SET game = ? WHERE user_id = ?', (selected_game, user_id))
        conn.commit()

    flash(f'Game updated to {selected_game}', 'success') # Success message
    return redirect(url_for('profile')) # Reload the page








# Route to update username of user (Form)
@app.route('/update_username', methods=['POST'])
def update_username():

    #check_if_user_exists()
    # -----------------------------------------------
    if not session.get('username'):
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))
    # ----------------------------------------------

    # Get the user id from session and the new username
    new_username = request.form.get('username')
    user_id = session['user_id']

    # Initialise the cursor
    conn = get_db()
    cursor = conn.cursor() 

    try:
        cursor.execute('UPDATE user SET username = ? WHERE user_id = ?', (new_username, user_id)) # Update the username of the user
        conn.commit()
        session['username'] = new_username  # Update session with new username
        flash('Username updated successfully.', 'success') # Success message

    # If error, where that username already exists, send warning message instead of crashing program
    except IntegrityError:
        flash('An account with that username already exists.', 'danger')
        conn.rollback()

    finally:
        conn.close()

    return redirect(url_for('profile')) # Reload the page

# Route to update email of user (Form)
@app.route('/update_email', methods=['POST'])
def update_email():

    #check_if_user_exists()
    # -----------------------------------------------
    if not session.get('username'):
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))
    # ----------------------------------------------

    # Get user id from session aned the new email
    new_email = request.form.get('email')
    user_id = session['user_id']

    # Initialise the cursor
    conn = get_db()
    cursor = conn.cursor() 
    
    try:
        cursor = conn.cursor() # Initialise cursor object
        cursor.execute('UPDATE user SET email = ? WHERE user_id = ?', (new_email, user_id)) # Update the email of the user
        conn.commit()
        flash('Email updated successfully.', 'success') # Success message

    # If error, where that email already exists, send warning message instead of crashing program
    except IntegrityError:
        flash('An account with that email already exists.', 'danger')
        conn.rollback()

    finally:
        conn.close()
    

    return redirect(url_for('profile')) # Reload the page




# Route to update the password of the user (Form)
@app.route('/update_password', methods=['POST'])
def update_password():

    #check_if_user_exists()
    # -----------------------------------------------
    if not session.get('username'):
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))
    # ----------------------------------------------
    
    # Get the user id from session, and the old & new passwords
    old_password = request.form.get('old_password')
    new_password = request.form.get('new_password')
    user_id = session['user_id']

    with get_db() as conn:
        cursor = conn.cursor() # Initialise cursor object

        # Get the current password hash for the user
        cursor.execute('SELECT password_hash FROM user WHERE user_id = ?', (user_id,))
        user = cursor.fetchone()

        # If current password is wrong, give error message without crashing website
        if not user or not check_password_hash(user['password_hash'], old_password):
            flash('Incorrect current password.', 'danger')
        
        # If current password is right
        else:
            new_password_hash = generate_password_hash(new_password) # Generate the password hash
            cursor.execute('UPDATE user SET password_hash = ? WHERE user_id = ?', (new_password_hash, user_id)) # Update the new password
            conn.commit()
            flash('Password updated successfully.', 'success') # Success message

    return redirect(url_for('profile')) # Reload page



# Route to update statistics of user after quick duel
@app.route('/update_statistic', methods=['POST'])
def update_statistic():

    #check_if_user_exists()
    # -----------------------------------------------
    if not session.get('username'):
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))
    # ----------------------------------------------

    # Get profile id from session, and match id and action
    profile_id = session.get('profile_id')  # This gets the profile_id from the form
    match_id = request.form.get('match_id')      # This gets the match_id from the form
    action = request.form.get('action')          # This gets the action (kill, death, or assist) from the form


    # If any of them don't exist, give an error message to user without crashing website
    if not profile_id or not match_id or not action:
        flash('Invalid request.', 'danger') # Error message
        return redirect(url_for('quick_duel')) # Redirect user

    with get_db() as conn:
        cursor = conn.cursor() # Initialise cursor object

        try:
            # Check if player is part of match
            cursor.execute('''SELECT 1
                FROM team_member
                INNER JOIN match ON (team_member.team_id = match.team1_id OR team_member.team_id = match.team2_id)
                WHERE match.match_id = ?
                AND team_member.profile_id = ?''', (match_id, profile_id))
            
            result = cursor.fetchone()

            # If player is not part of the match, give error message without crashing website
            if not result:
                flash('This player is not part of the match.', 'warning') # Error message
                return redirect(url_for('quick_duel')) # Redirect user

            # If not valid action, give error message without crashing website
            if action not in ['kill', 'death', 'assist']:
                flash('Invalid action.', 'danger') # Error message
                return redirect(url_for('quick_duel')) # Redirect user


            # Increment the appropriate stat
            column = {
                'kill': 'kills',
                'death': 'deaths',
                'assist': 'assists'
            }[action]

            # Insert/Update the stat for the correct player
            cursor.execute(f'''
                INSERT INTO match_statistic (match_id, profile_id, {column})
                VALUES (?, ?, 1)
                ON CONFLICT(match_id, profile_id)
                DO UPDATE SET {column} = {column} + 1''', (match_id, profile_id))

            conn.commit()

            flash(f'{column.capitalize()} updated successfully.', 'success') # Success message

        # If error, catch the error and don't crash website, give error message to user and give exact error in console
        except Exception as e:
            app.logger.error(f"Error updating statistic: {e}") # Give error in console
            flash('An error occurred while updating the statistic.', 'danger') # Give error message to user

    return redirect(url_for('quick_duel')) # Reload the page
