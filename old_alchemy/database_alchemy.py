    from flask import Flask, render_template , request, redirect, url_for, flash, session
    # Import Flask and render_template for handling requests and rendering HTML templates
    from flask_sqlalchemy import SQLAlchemy   
    # Import SQLAlchemy for database handling
    import os # Import os module to handle file paths

    import sqlite3

    # For passwords
    from werkzeug.security import generate_password_hash, check_password_hash

    from models import * # All the models for databse

    app = Flask(__name__)  # Initialize the Flask application

    # Set a secret key for session management (required for using session)
    app.secret_key = 'berkay'  # Replace 'your_secret_key' with a random string

    # Database configuration
    base_dir = os.path.abspath(os.path.dirname(__file__))  
    # Get the absolute path of the directory where the script is located
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(base_dir, 'datah.db')  # Set the database URI for SQLAlchemy
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Disable tracking modifications to save memory

    db.init_app(app) # Initialize SQLAlchemy with the Flask app

    with app.app_context():
        db.create_all()


    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            username = request.form['username']
            email = request.form['email']
            password = request.form['password']
            password_hash = generate_password_hash(password)
            
            new_user = User(username=username, email=email, password_hash=password_hash)
            db.session.add(new_user)
            db.session.commit()
            
            return redirect(url_for('index'))
        
        return render_template('register.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            email = request.form['email']
            password = request.form['password']
            
            user = User.query.filter_by(email=email).first()
            
            if user and check_password_hash(user.password_hash, password):
                # Correct credentials, log the user in
                session['user_id'] = user.user_id
                session['username'] = user.username

            
                return redirect(url_for('index'))
            
            else:
                # Invalid credentials
                flash('Invalid email or password. Please try again.', 'danger')
        
        return render_template('login.html')


    @app.route('/')  # Define the route for the homepage
    def index():
        return render_template('index.html')

    @app.route('/profile')
    def profile():
        if not session.get('username'):
            flash('You need to log in first.', 'warning')
            return redirect(url_for('login'))
        
        user_id = session['user_id']
        
        # Fetch player's profile
        player_profile = PlayerProfile.query.filter_by(user_id=user_id).first()

        player_statistics = None
        if player_profile:
            # Fetch player's statistics if the profile exists
            player_statistics = PlayerStatistics.query.filter_by(profile_id=player_profile.profile_id).first()

        return render_template('profile.html', player_profile=player_profile, player_statistics=player_statistics)


    @app.route('/create_profile', methods=['POST'])
    def create_profile():
        if not session.get('username'):
            flash('You need to log in first.', 'warning')
            return redirect(url_for('login'))

        user_id = session['user_id']

        # Check if the user already has a profile
        existing_profile = PlayerProfile.query.filter_by(user_id=user_id).first()
        if existing_profile:
            flash('Profile already exists.', 'info')
            return redirect(url_for('profile'))

        # Create a new profile
        new_profile = PlayerProfile(
            user_id=user_id,
            game="Fortnite",  # Set a default game initially, can be changed later
        )
        db.session.add(new_profile)
        db.session.commit()

        # After committing the profile, create a PlayerStatistics record
        new_statistics = PlayerStatistics(
            profile_id=new_profile.profile_id,
            total_kills=0,
            total_deaths=0,
            total_assists=0
        )
        db.session.add(new_statistics)
        db.session.commit()

        flash('Profile created successfully!', 'success')
        return redirect(url_for('profile'))


    @app.route('/tournaments')
    def tournaments():
        if not session.get('username'):
            flash('You need to log in first.', 'warning')
            return redirect(url_for('login'))
        
        # Fetch all tournaments from the database
        tournaments = Tournament.query.all()
        print("Tournaments fetched:", tournaments)  # Debugging line
        
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

        # Find the player's profile
        player_profile = PlayerProfile.query.filter_by(user_id=user_id).first()

        if player_profile:
            player_profile.game = selected_game
            db.session.commit()
            flash(f'Game updated to {selected_game}', 'success')
        else:
            flash('Profile not found.', 'danger')

        return redirect(url_for('profile'))


    if __name__ == '__main__':  # Check if the script is run directly (not imported)
        app.run(debug=True)  # Run the Flask application with debug mode enabled






    #@app.route('/logged_in')
    #def logged_in():
    #    username = session.get('username')
    #    return render_template('logged_in.html', username=username)