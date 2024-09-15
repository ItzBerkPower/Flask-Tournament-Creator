from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'user'
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

class PlayerProfile(db.Model):
    profile_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'))
    game = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

class Team(db.Model):
    team_id = db.Column(db.Integer, primary_key=True)
    team_name = db.Column(db.String(50), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

class TeamMember(db.Model):
    team_member_id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.team_id'))
    profile_id = db.Column(db.Integer, db.ForeignKey('player_profile.profile_id'))
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

class Tournament(db.Model):
    tournament_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    game = db.Column(db.String(50), nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

class TournamentParticipant(db.Model):
    participant_id = db.Column(db.Integer, primary_key=True)
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournament.tournament_id'))
    team_id = db.Column(db.Integer, db.ForeignKey('team.team_id'), nullable=True)
    profile_id = db.Column(db.Integer, db.ForeignKey('player_profile.profile_id'), nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

class Match(db.Model):
    match_id = db.Column(db.Integer, primary_key=True)
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournament.tournament_id'))
    round = db.Column(db.Integer, nullable=False)
    team1_id = db.Column(db.Integer, db.ForeignKey('team.team_id'))
    team2_id = db.Column(db.Integer, db.ForeignKey('team.team_id'))
    winner_team_id = db.Column(db.Integer, db.ForeignKey('team.team_id'), nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

class MatchResult(db.Model):
    match_result_id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(db.Integer, db.ForeignKey('match.match_id'))
    profile_id = db.Column(db.Integer, db.ForeignKey('player_profile.profile_id'))
    statistics_id = db.Column(db.Integer, db.ForeignKey('match_statistic.statistic_id'))  # Link to MatchStatistic
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

class MatchStatistic(db.Model):
    statistic_id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(db.Integer, db.ForeignKey('match.match_id'))
    profile_id = db.Column(db.Integer, db.ForeignKey('player_profile.profile_id'))
    kills = db.Column(db.Integer, nullable=False, default=0)
    deaths = db.Column(db.Integer, nullable=False, default=0)
    assists = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

class PlayerStatistics(db.Model):
    player_statistics_id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey('player_profile.profile_id'))
    total_kills = db.Column(db.Integer, nullable=False, default=0)
    total_deaths = db.Column(db.Integer, nullable=False, default=0)
    total_assists = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
