# ALL IMPORTS
from flask import render_template , request, redirect, url_for, flash, session # Import Flask and render_template for handling requests and rendering HTML templates
from sqlite3 import IntegrityError # Import sqlite3 for database handling
from models import * # All the models for database
from datetime import datetime



# Route for the landing team page
@app.route('/team')
def team():

    # check_if_profile_and_user_exists()
    # ------------------------------------------------
    if not session.get('username'):
        print('login error')
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))

    if not session.get('profile_id'):
        flash('You need to create a profile first.', 'warning')
        return redirect(url_for('profile'))
    
    # ------------------------------------------------

    profile_id = session.get('profile_id') # Get the user profile id from session

    with get_db() as conn:
        cursor = conn.cursor() # Initialise cursor object

        # Check if current player is already on team
        cursor.execute('''
            SELECT team.team_id, team.team_name 
            FROM team_member 
            INNER JOIN team ON team_member.team_id = team.team_id 
            WHERE team_member.profile_id = ?
        ''', (profile_id,))

        team_info = cursor.fetchone()

        # If player on team, get usernames of all members on team
        if team_info:
            team_id = team_info['team_id']
            team_name = team_info['team_name']

            cursor.execute('''
                SELECT user.username 
                FROM team_member 
                INNER JOIN player_profile ON team_member.profile_id = player_profile.profile_id
                INNER JOIN user ON player_profile.user_id = user.user_id
                WHERE team_member.team_id = ?
            ''', (team_id,))
            team_members = cursor.fetchall() # Get all usernames

            return render_template('team_info.html', team_name=team_name, team_members=team_members) # Render actual template with parameters

    # If Player not on any team, show create/join team options
    return render_template('team.html')




# Route for creating a team (Is a form page)
@app.route('/create_team', methods=['GET', 'POST'])
def create_team():

    # check_if_profile_and_user_exists()
    # -----------------------------------------------------------
    if not session.get('username'):
        print('login error')
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))

    if not session.get('profile_id'):
        flash('You need to create a profile first.', 'warning')
        return redirect(url_for('profile'))
    # -----------------------------------------------------------
    
    # Ask for the team name to make the team
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

            # If team exists, give warning message without crashing website
            if existing_team:
                flash('Team name already exists. Please choose another name.', 'danger')
            
            # If team doesn't exist, insert new team into table
            else:
                cursor.execute('INSERT INTO team (team_name) VALUES (?)', (team_name,))
                conn.commit()
                flash(f'Team "{team_name}" created successfully!', 'success') # Give success message

        return redirect(url_for('team')) # Reload the page to update it

    return render_template('create_team.html')




# Route for joining a team (Is a form)
@app.route('/join_team', methods=['GET', 'POST'])
def join_team():

    # check_if_profile_and_user_exists()
    # ---------------------------------------------
    if not session.get('username'):
        print('login error')
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))

    if not session.get('profile_id'):
        flash('You need to create a profile first.', 'warning')
        return redirect(url_for('profile'))
    # ----------------------------------------------
    

    # Ask for team name to join the team
    if request.method == 'POST':
        team_name = request.form['team_name']


        with get_db() as conn:
            cursor = conn.cursor() # Initialise cursor object

            # Try to find team with team name
            cursor.execute('SELECT * FROM team WHERE team_name = ?', (team_name,))
            team = cursor.fetchone()

            # If team name not found, give error message without crashing program
            if not team:
                flash('Team not found. Please check the team name or create a new one.', 'danger')


            # If found team
            else:
                team_id = team['team_id']
                profile_id = session['profile_id']

                # See if user is already part of team
                cursor.execute('SELECT * FROM team_member WHERE team_id = ? AND profile_id = ?', (team_id, profile_id))
                existing_member = cursor.fetchone()

                # If is part of team, give warning message instead of crashing website
                if existing_member:
                    flash(f'You are already a member of the team "{team_name}".', 'info')

                # If not part of team, add the team member to team
                else:
                    cursor.execute('INSERT INTO team_member (team_id, profile_id) VALUES (?, ?)', (team_id, profile_id))
                    conn.commit()
                    flash(f'You have successfully joined the team "{team_name}".', 'success') # Give success message
            
        return redirect(url_for('team')) # Reload the page to update it
    
    return render_template('join_team.html') # Render template




# Route to leave the team (Is single button)
@app.route('/leave_team', methods=['POST'])
def leave_team():
    profile_id = session.get('profile_id')  # Get profile_id
    team_id = get_user_team_id(profile_id)  # Get team_id using helper function
    
    # If team id exists,
    if team_id:
        with get_db() as conn:
            cursor = conn.cursor() # Initalise cursor object
            cursor.execute("DELETE FROM team_member WHERE profile_id = ? AND team_id = ?", (profile_id, team_id)) # Delete user from team
            conn.commit()

        flash('You have successfully left the team.', 'success') # Give success message

    # If team id doesn't exist, give warning message without crashing program
    else:
        flash('You are not a member of this team.', 'error')

    return redirect(url_for('index'))  # Redirect user to landing page