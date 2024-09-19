# ALL IMPORTS
from flask import Flask, render_template , request, redirect, url_for, flash, session # Import Flask and render_template for handling requests and rendering HTML templates
import os # Import os module to handle file paths
from sqlite3 import IntegrityError # Import sqlite3 for database handling
from werkzeug.security import generate_password_hash, check_password_hash # For passwords
from models import * # All the models for databse
from datetime import datetime

from flask_wtf import FlaskForm
from wtforms import StringField, EmailField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo


@app.route('/tournaments')
def tournaments():

    # check_if_profile_and_user_exists()
    # -----------------------------------------------------------------
    if not session.get('username'):
        print('login error')
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))

    if not session.get('profile_id'):
        flash('You need to create a profile first.', 'warning')
        return redirect(url_for('profile'))
    
    # ---------------------------------------------------------------
    
    #Get profile id from session, declare other variables
    profile_id = session.get('profile_id')
    tournament_info = None
    teams_in_tournament = []


    with get_db() as conn:
        cursor = conn.cursor() # Initialise cursor object

        cursor.execute('SELECT * FROM tournament') # Fetch all the tournaments
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

            # Debugging teams in tournaments (Just for console)
            print(teams_in_tournament)

    # Render the template
    return render_template('tournaments.html',
        tournaments=tournaments,
        joined_tournament=joined_tournament,
        teams_in_tournament=teams_in_tournament
    )




# Route to create the actual tournament
@app.route('/create_tournament', methods=['GET', 'POST'])
def create_tournament():

    #check_if_profile_and_user_exists()
    # ---------------------------------------------------------------------
    if not session.get('username'):
        print('login error')
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))

    if not session.get('profile_id'):
        flash('You need to create a profile first.', 'warning')
        return redirect(url_for('profile'))

    # ---------------------------------------------------------------------

    # Get the tournament name, type of game, start & end date from user forms
    if request.method == 'POST':
        tournament_name = request.form['tournament_name']
        game = request.form['game']
        start_date = request.form['start_date']
        end_date = request.form.get('end_date')  # Optional

        # Validate inputs
        if not tournament_name or not game or not start_date:
            flash('Tournament name, game, and start date are required!', 'danger') # Error message if any are forgotten
            return redirect(url_for('create_tournament')) # Reload page

        # Insert the tournament into the database
        with get_db() as conn:
            cursor = conn.cursor() # Initalise cursor object
            
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
            flash(f'Tournament "{tournament_name}" created successfully!', 'success') # Success message
            return redirect(url_for('tournaments')) # Redirect user
        
    return render_template('create_tournament.html') # Render the template





# Route to join a tournament
@app.route('/join_tournament/<int:tournament_id>', methods=['POST'])
def join_tournament(tournament_id):

    # ---------------------------------------------------------------------
    #check_if_profile_and_user_exists()
    if not session.get('username'):
        print('login error')
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))

    if not session.get('profile_id'):
        flash('You need to create a profile first.', 'warning')
        return redirect(url_for('profile'))
    # ---------------------------------------------------------------------

    # Get profile id from session
    profile_id = session.get('profile_id')

    with get_db() as conn:
        cursor = conn.cursor() # Initalise cursor object

        # Find if the player is part of a team
        cursor.execute('''
            SELECT team_id FROM team_member WHERE profile_id = ?
        ''', (profile_id,))
        team = cursor.fetchone()

        # If not part of team, give warning message without crashing website
        if not team:
            flash('You need to be part of a team to join a tournament.', 'danger') # Error message
            return redirect(url_for('tournaments')) # Redirect back to original page

        team_id = team['team_id'] # If part of team, then put team id into variable

        # Check if the team has already joined the tournament
        cursor.execute('''
            SELECT * FROM tournament_participant WHERE tournament_id = ? AND team_id = ?
        ''', (tournament_id, team_id))
        existing_participant = cursor.fetchone()

        # If has joined the tournament, give warning message without crashing website
        if existing_participant:
            flash('Your team has already joined this tournament.', 'info') # Error message

        # If hasn't joined tournament
        else:
            # Create tournament participant record in table for that user, so that they join tournament
            cursor.execute('''
                INSERT INTO tournament_participant (tournament_id, team_id, profile_id) VALUES (?, ?, ?)
            ''', (tournament_id, team_id, profile_id))
            conn.commit()

            flash('Your team has successfully joined the tournament!', 'success') # Success message

    return redirect(url_for('tournaments')) # Reload page