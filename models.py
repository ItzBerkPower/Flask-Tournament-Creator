import sqlite3 # Import sqlite3 for database handling
import os
from flask import Flask, render_template , request, redirect, url_for, flash, session # Import Flask and render_template for handling requests and rendering HTML templates
from sqlite3 import IntegrityError # Import sqlite3 for database handling
from werkzeug.security import generate_password_hash, check_password_hash # For passwords

from datetime import datetime

from flask_wtf import FlaskForm
from wtforms import StringField, EmailField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo


#DATABASE = 'datah.db', kept creating it in outer file if you run the code in outer directory
base_dir = os.path.abspath(os.path.dirname(__file__)) # So instead define the directory
db_path = os.path.join(base_dir, 'datah.db')

app = Flask(__name__)  # Initialize the Flask application
app.secret_key = 'berkay' # Secret key for session manageent 

# Connect to database
def get_db():
    conn = sqlite3.connect(db_path) # Create connection between database and flask
    conn.row_factory = sqlite3.Row # Allows fetching rows as dictionaries
    return conn 


# Initialise database
def init_db():
    with get_db() as conn:
        cursor = conn.cursor() # Initialise cursor object

        # Create the user table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        ''')

        # Create the player_profile table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS player_profile (
            profile_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            game TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES user(user_id)
        );
        ''')

        # Create the team table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS team (
            team_id INTEGER PRIMARY KEY AUTOINCREMENT,
            team_name TEXT NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        ''')

        # Create the team_member table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS team_member (
            team_member_id INTEGER PRIMARY KEY AUTOINCREMENT,
            team_id INTEGER NOT NULL,
            profile_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (team_id) REFERENCES team(team_id),
            FOREIGN KEY (profile_id) REFERENCES player_profile(profile_id)
        );
        ''')

        # Create the tournament table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS tournament (
            tournament_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            game TEXT NOT NULL,
            start_date TIMESTAMP NOT NULL,
            end_date TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        ''')

        # Create the tournament_participant table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS tournament_participant (
            participant_id INTEGER PRIMARY KEY AUTOINCREMENT,
            tournament_id INTEGER NOT NULL,
            team_id INTEGER,
            profile_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (tournament_id) REFERENCES tournament(tournament_id),
            FOREIGN KEY (team_id) REFERENCES team(team_id),
            FOREIGN KEY (profile_id) REFERENCES player_profile(profile_id)
        );
        ''')

        # Create the match table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS match (
            match_id INTEGER PRIMARY KEY AUTOINCREMENT,
            tournament_id INTEGER,
            round INTEGER NOT NULL,
            team1_id INTEGER NOT NULL,
            team2_id INTEGER,
            winner_team_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (tournament_id) REFERENCES tournament(tournament_id),
            FOREIGN KEY (team1_id) REFERENCES team(team_id),
            FOREIGN KEY (team2_id) REFERENCES team(team_id),
            FOREIGN KEY (winner_team_id) REFERENCES team(team_id)
        );
        ''')

        # Create the match_statistic table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS match_statistic (
            statistic_id INTEGER PRIMARY KEY AUTOINCREMENT,
            match_id INTEGER NOT NULL,
            profile_id INTEGER NOT NULL,
            kills INTEGER NOT NULL DEFAULT 0,
            deaths INTEGER NOT NULL DEFAULT 0,
            assists INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (match_id) REFERENCES match(match_id),
            FOREIGN KEY (profile_id) REFERENCES player_profile(profile_id)
            UNIQUE(match_id, profile_id)
        );
        ''')

        # Create the player_statistics table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS player_statistics (
            player_statistics_id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_id INTEGER NOT NULL,
            total_kills INTEGER NOT NULL DEFAULT 0,
            total_deaths INTEGER NOT NULL DEFAULT 0,
            total_assists INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (profile_id) REFERENCES player_profile(profile_id)
        );
        ''')

    conn.commit()
    #conn.close(), don't need as in 'with' command, which is pythonic way of automatically closing website


# HELPER FUNCTIONS

# Helper function to get the id of the team a user is in
def get_user_team_id(profile_id):
    with get_db() as conn:
        cursor = conn.cursor() # Initalise cursor object
        cursor.execute("SELECT team_id FROM team_member WHERE profile_id = ?", (profile_id,)) # Fetch the team id if it exists
        result = cursor.fetchone()

    return result['team_id'] if result else None # Return the team id if it exists, if not, return 'None'


# Helper function to check if user profile and user account exists
def check_if_profile_and_user_exists():
    # If username not in session, user account doesn't exist, give warning & redirect
    if not session.get('username'):
        print('login error')
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))

    # If profile id not in session, user profile doesn't exist, give warning & redirect
    if not session.get('profile_id'):
        flash('You need to create a profile first.', 'warning')
        return redirect(url_for('profile'))
    
# Helper function to check if user account exists
def check_if_user_exists():
    # If username not in session, user account doesn't exist, give warning & redirect
    if not session.get('username'):
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))
    

# Check if the player is part of a team
def check_player_part_of_team(profile_id):
    result = None

    with get_db() as conn:
        cursor = conn.cursor() # Initalise cursor object

        # Find if player is part of a team
        cursor.execute('''
            SELECT team_member.team_id
            FROM team_member
            WHERE team_member.profile_id = ?
        ''', (profile_id,))

        result = cursor.fetchone() # Put in a variable the player team_id if part of team

    return result # Return the result as variable