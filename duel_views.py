# ALL IMPORTS
from flask import Flask, render_template , request, redirect, url_for, flash, session # Import Flask and render_template for handling requests and rendering HTML templates
import os # Import os module to handle file paths
from sqlite3 import IntegrityError # Import sqlite3 for database handling
from werkzeug.security import generate_password_hash, check_password_hash # For passwords
from models import * # All the models for databse
from datetime import datetime


# Route for actual quick_duel page
@app.route('/quick_duel')
def quick_duel():

    #check_if_profile_and_user_exists()
    # ---------------------------------------------------------
    if not session.get('username'):
        print('login error')
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))

    if not session.get('profile_id'):
        flash('You need to create a profile first.', 'warning')
        return redirect(url_for('profile'))
    # ----------------------------------------------------------

    # INITIALISE ALL VARIABLES
    profile_id = session.get('profile_id') # Get profile id from session
    team_id = None
    duel_id = None
    match_data = None
    team1_name = team2_name = None
    round_number = None

    team1_players = []
    team2_players = []


    
    with get_db() as conn:
        cursor = conn.cursor() # Initialise cursor object

        # Check if player part of a team

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
            SELECT match.match_id, match.team1_id, match.team2_id, match.round, 
                   team1.team_name AS team1_name, team2.team_name AS team2_name
            FROM match
            LEFT JOIN team AS team1 ON match.team1_id = team1.team_id
            LEFT JOIN team AS team2 ON match.team2_id = team2.team_id
            WHERE match.team1_id = ? OR match.team2_id = ?
        ''', (team_id, team_id))
        match_data = cursor.fetchone()

        # If team already in a duel    
        if match_data:
            # Initialise variables to pass onto template
            duel_id = match_data['match_id']
            team1_name = match_data['team1_name']
            team2_name = match_data['team2_name']
            round_number = match_data['round']

            # Fetch players for both teams
            cursor.execute('''
                SELECT user.username
                FROM team_member
                INNER JOIN player_profile ON team_member.profile_id = player_profile.profile_id
                INNER JOIN user ON player_profile.user_id = user.user_id
                WHERE team_member.team_id = ?
            ''', (match_data['team1_id'],))
            team1_players = cursor.fetchall()

            cursor.execute('''
                SELECT user.username
                FROM team_member
                INNER JOIN player_profile ON team_member.profile_id = player_profile.profile_id
                INNER JOIN user ON player_profile.user_id = user.user_id
                WHERE team_member.team_id = ?
            ''', (match_data['team2_id'],))
            team2_players = cursor.fetchall()

    # Render the template for website, passing all variables as parameters to display in HTML page
    return render_template(
        'quick_duel.html',
        duel_id=duel_id,
        team1_name=team1_name,
        team2_name=team2_name,
        round_number=round_number,
        team1_players=team1_players,
        team2_players=team2_players
    )






# Route to create a quick duel
@app.route('/create_duel', methods=['POST'])
def create_duel():

    #check_if_user_exists()
    # -----------------------------------------------
    if not session.get('username'):
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))
    # ----------------------------------------------

    profile_id = session.get('profile_id')
    team_id = None

    result = check_player_part_of_team(profile_id) # Check if player is part of team

    if result: # If player is part of team, update team_id
        team_id = result['team_id']
    else: # If player isn't part of team, send waring message and redirect user to profile
        flash('You need to be part of a team to create a duel.', 'warning')
        return redirect(url_for('profile'))



    with get_db() as conn:
        cursor = conn.cursor() # Initialise cursor object

        # Create new duel (Match) and assign this user's team as team 1
        cursor.execute('''
            INSERT INTO match (team1_id, round)
            VALUES (?, 0)
        ''', (team_id,))

        conn.commit()

        flash('Quick duel created. You are Team 1.', 'success') # Success message

    return redirect(url_for('quick_duel')) # Reload the page









# Route to join existing quick duel
@app.route('/join_duel', methods=['POST'])
def join_duel():

    #check_if_user_exists()
    # -----------------------------------------------
    if not session.get('username'):
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))
    # ----------------------------------------------

    profile_id = session.get('profile_id') # Get profile id
    team_id = None
    duel_id = request.form.get('duel_id')

    # If user hasn't provided duel ID, send warning messae, and redirect back to original page
    if not duel_id:
        flash('Please provide a duel ID to join.', 'danger') # Warning message
        return redirect(url_for('quick_duel'))


    result = check_player_part_of_team(profile_id) # Check if player is part of team

    if result: # If player is part of team, update team_id
        team_id = result['team_id']
    else: # If player isn't part of team, send waring message and redirect user to profile
        flash('You need to be part of a team to create a duel.', 'warning')
        return redirect(url_for('profile'))
    

    with get_db() as conn:
        cursor = conn.cursor() # Initialise cursor object

        # Check if duel exists and if team 2 is empty
        cursor.execute('''
            SELECT match_id, team2_id
            FROM match
            WHERE match_id = ? AND team2_id IS NULL
        ''', (duel_id,))
        match_data = cursor.fetchone()

        # If duel exists and team 2 is empty,
        if match_data:
            
            cursor.execute(''' 
                UPDATE match
                SET team2_id = ?
                WHERE match_id = ?
            ''', (team_id, duel_id)) # Assign the user's team as team 2

            conn.commit()
            flash(f'You have joined Duel {duel_id} as Team 2.', 'success') # Success message

        # If duel doesn't exist, or team 2 is full, then send warning message without crashing website
        else:
            flash('Invalid duel ID or duel already has two teams.', 'danger') # Warning message

    return redirect(url_for('quick_duel')) # Redirect user back to original page











# Route to end the duel
@app.route('/end_duel', methods=['POST'])
def end_duel():
    match_id = request.form.get('match_id') # Get the match id


    # If no match id, means match doesn't actually exist (Just error detection)
    if not match_id:
        flash('Invalid request.', 'danger')
        return redirect(url_for('quick_duel')) # Resend user back to original page


    with get_db() as conn:
        cursor = conn.cursor() # Initialise cursor object

        try:
            # Get stats for all players in the match
            cursor.execute('''
                SELECT profile_id, kills, deaths, assists
                FROM match_statistic
                WHERE match_id = ?
            ''', (match_id,))
            player_stats = cursor.fetchall()  # Get all stats for players in this match

            # Assign the values to external variables
            for player in player_stats:
                profile_id = player['profile_id']
                kills = player['kills']
                deaths = player['deaths']
                assists = player['assists']


                # Check if player already has statistics in the 'player_statistics' table
                cursor.execute('''
                    SELECT total_kills, total_deaths, total_assists
                    FROM player_statistics
                    WHERE profile_id = ?
                ''', (profile_id,))
                existing_stats = cursor.fetchone()

                # If the stats exist, update the values
                if existing_stats:
                    cursor.execute('''
                        UPDATE player_statistics
                        SET total_kills = total_kills + ?,
                            total_deaths = total_deaths + ?,
                            total_assists = total_assists + ?
                        WHERE profile_id = ?
                    ''', (kills, deaths, assists, profile_id)) # Updates all the values

                # If no stats exist (Eg. Player doesn't have row in table), then add new row with the stats
                else:
                    cursor.execute('''
                        INSERT INTO player_statistics (profile_id, total_kills, total_deaths, total_assists)
                        VALUES (?, ?, ?, ?)
                    ''', (profile_id, kills, deaths, assists))

            # Delete match from 'match' table
            cursor.execute('DELETE FROM match WHERE match_id = ?', (match_id,))
            conn.commit()

            flash('Duel ended, and statistics have been updated.', 'success') # Success message

        # If error occurs, catch error without crashing website and display error in console
        except Exception as e:
            app.logger.error(f"Error ending duel: {e}")
            flash('An error occurred while ending the duel and updating statistics.', 'danger') # Give error message to user

    return redirect(url_for('quick_duel')) # Reload the page







# Route to update round number
@app.route('/next_round', methods=['POST'])
def next_round():
    match_id = request.form.get('match_id') # Get match id from the match

    # If no match id, no match, so send error message without crashing website, and redirect back to original page
    if not match_id:
        flash('Invalid request.', 'danger')
        return redirect(url_for('quick_duel'))

    with get_db() as conn:
        cursor = conn.cursor() # Initialise cursor object

        try:
            # Increment round number by 1
            cursor.execute('''
                UPDATE match
                SET round = round + 1
                WHERE match_id = ?
            ''', (match_id,))
            conn.commit()

            flash('Round number updated successfully.', 'success') # Success message

        # If error occurs, catch error without crashing website and display error in console
        except Exception as e:
            app.logger.error(f"Error updating round number: {e}")
            flash('An error occurred while updating the round number.', 'danger') # Give error message to user

    return redirect(url_for('quick_duel')) # Reload the page

