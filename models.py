import sqlite3 # Import sqlite3 for database handling

DATABASE = 'datah.db'

# Connect to database
def get_db():
    conn = sqlite3.connect(DATABASE) #
    conn.row_factory = sqlite3.Row # Allows fetching rows as dictionaries
    return conn 


# Initialise database
def init_db():
    with get_db() as conn:
        cursor = conn.cursor()

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
            tournament_id INTEGER NOT NULL,
            round INTEGER NOT NULL,
            team1_id INTEGER NOT NULL,
            team2_id INTEGER NOT NULL,
            winner_team_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (tournament_id) REFERENCES tournament(tournament_id),
            FOREIGN KEY (team1_id) REFERENCES team(team_id),
            FOREIGN KEY (team2_id) REFERENCES team(team_id),
            FOREIGN KEY (winner_team_id) REFERENCES team(team_id)
        );
        ''')

        # Create the match_result table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS match_result (
            match_result_id INTEGER PRIMARY KEY AUTOINCREMENT,
            match_id INTEGER NOT NULL,
            profile_id INTEGER NOT NULL,
            statistics_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (match_id) REFERENCES match(match_id),
            FOREIGN KEY (profile_id) REFERENCES player_profile(profile_id),
            FOREIGN KEY (statistics_id) REFERENCES match_statistic(statistic_id)
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

# Call this function to initialize the d