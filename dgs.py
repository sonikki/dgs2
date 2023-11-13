from flask import Flask, flash, abort, request, redirect, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql.elements import ClauseElement
from flask_migrate import Migrate
from datetime import datetime

import pandas as pd
from sqlalchemy import func
from flask import jsonify


def is_valid_login(username, password):
    # For now, just return True to allow access but can be customized in future
    return True


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///dgs.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)


class MetaData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    last_processed_timestamp = db.Column(
        db.DateTime, nullable=False, server_default=func.now()
    )

def get_last_processed_timestamp():
    meta_data = MetaData.query.first()
    if meta_data:
        return meta_data.last_processed_timestamp
    else:
        return None


def update_last_processed_timestamp(timestamp):
    # Convert the timestamp to a string
    timestamp_str = timestamp.strftime("%Y-%m-%d %H%M")

    # Fetch the MetaData row from the database
    meta_data = MetaData.query.first()

    # Update the last_processed_timestamp field and commit the changes
    meta_data.last_processed_timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H%M")
    db.session.commit()



# Define database models


# BaseModel is an abstract base class for all other models. It provides common methods that can be used by all models.
class BaseModel(db.Model):
    __abstract__ = True

    # get_or_create is a class method that tries to get an instance of the model based on the provided arguments.
    # If it can't find an instance, it creates a new one.

    @classmethod
    def get_or_create(cls, defaults=None, **kwargs):
        instance = db.session.query(cls).filter_by(**kwargs).first()
        if instance:
            return instance, False
        else:
            params = dict(
                (k, v) for k, v in kwargs.items() if not isinstance(v, ClauseElement)
            )
            params.update(defaults or {})
            instance = cls(**params)
            db.session.add(instance)
            return instance, True


# Course represents a disc golf course. It has a unique name.
class Course(BaseModel):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)


# CourseLayout represents a specific layout of a course. It is associated with a Course. It has various attributes, such as the number of holes and the par values for each hole.
class CourseLayout(BaseModel):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"))
    layout_name = db.Column(db.String(64))
    hole_count = db.Column(db.Integer)
    par_values = db.Column(db.String(128))
    course = db.relationship("Course", backref=db.backref("layouts", lazy=True))


# Player represents a disc golf player. It has a unique name.
class Player(BaseModel):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)


# Round represents a round of disc golf. It is associated with a Course and a CourseLayout. It has a unique date.
class Round(BaseModel):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"))
    layout_id = db.Column(db.Integer, db.ForeignKey("course_layout.id"))
    date = db.Column(db.Date)
    score_difference = db.Column(db.Integer)


# Scorecard represents a player's scorecard for a round. It is associated with a Player and a Round. It has various attributes, such as the total score and the total number of throws.
class Scorecard(BaseModel):
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey("player.id"))
    round_id = db.Column(db.Integer, db.ForeignKey("round.id"))
    total_score = db.Column(db.Integer)
    score_difference = db.Column(db.Integer)
   


# HoleScore represents a player's score for a specific hole. It is associated with a Scorecard. It has the hole number and the number of strokes.
class HoleScore(BaseModel):
    id = db.Column(db.Integer, primary_key=True)
    scorecard_id = db.Column(db.Integer, db.ForeignKey("scorecard.id"))
    hole_number = db.Column(db.Integer)
    strokes = db.Column(db.Integer)


# Data upload route (not needed at the moment)

# @app.route('/upload', methods=['GET', 'POST'])
# def upload_file():
#   if request.method == 'POST':
#        filename = 'UDisc Scorecards.csv'
#        load_data(filename)
#        return redirect(url_for('index'))
#    return render_template('upload.html')


def load_data(filename):
    try:
        # Initialize counters
        player_counter = 0
        course_counter = 0
        layout_counter = 0
        round_counter = 0
        scorecard_counter = 0
        hole_score_counter = 0

        meta_data = MetaData.query.first()
        if meta_data is None:
            meta_data = MetaData(last_processed_timestamp=datetime.min)
            db.session.add(meta_data)

        df = pd.read_csv(filename)
        df['Kaikki'] = df['Kaikki'].fillna(0)
        df['Päivämäärä'] = pd.to_datetime(df['Päivämäärä'], format='%Y-%m-%d %H%M')
        df = df.sort_values('Päivämäärä')

        last_processed_timestamp = get_last_processed_timestamp()
        if last_processed_timestamp is None:
            last_processed_timestamp = datetime.min

        for _, row in df.iterrows():
            row_timestamp = row['Päivämäärä'].to_pydatetime()
            if row_timestamp >= meta_data.last_processed_timestamp:
                process_row(row)

                # Increment counters
                player_counter += 1
                course_counter += 1
                layout_counter += 1
                round_counter += 1
                scorecard_counter += 1
                hole_score_counter += len([col for col in df.columns if 'Hole' in col and pd.notna(row[col])])

                meta_data.last_processed_timestamp = row_timestamp
                db.session.commit()

        db.session.commit()
        update_last_processed_timestamp(df['Päivämäärä'].max())

        # Print counters
        print(f"Inserted {player_counter} rows into Player table")
        print(f"Inserted {course_counter} rows into Course table")
        print(f"Inserted {layout_counter} rows into CourseLayout table")
        print(f"Inserted {round_counter} rows into Round table")
        print(f"Inserted {scorecard_counter} rows into Scorecard table")
        print(f"Inserted {hole_score_counter} rows into HoleScore table")

    except Exception as e:
        print("Error loading data:", str(e))
        db.session.rollback()






def process_row(row):
    try:
        # Extract player information
        player_name = row['PlayerName'].strip()
        player = Player.get_or_create(name=player_name)[0]

        # Extract course information
        course_name = row['CourseName']
        course = Course.get_or_create(name=course_name)[0]

        # Extract layout information
        layout_name = row['LayoutName']
        layout = CourseLayout.get_or_create(course_id=course.id, layout_name=layout_name)[0]

        # Convert Timestamp to a string for date parsing
        date_object = row['Päivämäärä'].date()

        # Extract round information
        total_score = row['Kaikki']
        score_difference = row['+/-']

        # Handle NaN values in total_score (convert to 0)
        total_score = 0 if pd.isna(total_score) else total_score

        # Create or get the round object
        round_obj = Round.get_or_create(
            course_id=course.id,
            layout_id=layout.id,
            date=date_object
        )[0]

        # Continue processing if the player is not 'Par'
        if player_name != 'Par':
            # Create or update the scorecard and associate it with the round
            scorecard = Scorecard.get_or_create(
                player_id=player.id,
                round_id=round_obj.id,
                total_score=total_score,
                score_difference=score_difference
            )[0]

            # Create or update hole scores
            for i in range(1, len(row) - 6):
                if pd.notna(row[f'Hole{i}']):
                    hole_number = i
                    strokes = int(row[f'Hole{i}'])

                    # Ensure the HoleScore is associated with the Scorecard
                    hole_score = HoleScore.get_or_create(
                        scorecard_id=scorecard.id,
                        hole_number=hole_number,
                        strokes=strokes
                    )[0]

    except Exception as e:
        # Handle errors gracefully and provide useful information
        print(f"Error processing row: {str(e)}")
        raise e





# Route to check if coursedata is present in the database (not needed at the moment)
# @app.route('/check_data', methods=['GET'])
# def check_data():
#    course_count = db.session.query(func.count(Course.id)).scalar()
#    layout_count = db.session.query(func.count(CourseLayout.id)).scalar()
#
#    if course_count > 0 and layout_count > 0:
#        return 'Data is present in the database'
#    else:
#        return 'No data found in the database'

# Additional routes for your application (layouts, detailed scorecard view, etc.)



@app.route('/hole_scores/<int:scorecard_id>')
def hole_scores(scorecard_id):
    scorecard = Scorecard.query.get_or_404(scorecard_id)

    hole_scores = db.session.query(
        HoleScore.hole_number,
        HoleScore.strokes,
        CourseLayout.layout_name,
        Course.name
    ).select_from(HoleScore).join(
        Scorecard,
        Scorecard.id == HoleScore.scorecard_id
    ).join(
        Round,
        Round.id == Scorecard.round_id
    ).join(
        CourseLayout,
        CourseLayout.id == Round.layout_id
    ).join(
        Course,
        Course.id == Round.course_id
    ).filter(
        HoleScore.scorecard_id == scorecard.id
    ).all()

    return jsonify([
        {
            'hole_number': hole_number,
            'strokes': strokes,
            'layout_name': layout_name,
            'course_name': course_name
        }
        for hole_number, strokes, layout_name, course_name in hole_scores
    ])
    

@app.route("/layouts_for_course/<course_name>")
def layouts_for_course(course_name):
    course = Course.query.filter_by(name=course_name).first()
    if course is None:
        abort(404, description="Course not found")
    layouts = CourseLayout.query.filter_by(course_id=course.id).all()
    return jsonify([layout.layout_name for layout in layouts])


@app.route("/courses_for_player/<player_name>")
def courses_for_player(player_name):
    player = Player.query.filter_by(name=player_name).first()
    if player is None:
        abort(404, description="Player not found")
    round_ids = (
        db.session.query(Scorecard.round_id).filter_by(player_id=player.id).distinct()
    )
    course_ids = (
        db.session.query(Round.course_id).filter(Round.id.in_(round_ids)).distinct()
    )
    courses = Course.query.filter(Course.id.in_(course_ids)).all()
    return jsonify([course.name for course in courses])


# Route for course management (not needed at the moment)
# @app.route('/courses')
# def courses():
#    courses = Course.query.all()
#    return render_template('courses.html', courses=courses)


# Route for layout management

# @app.route('/layouts')  # not needed at the moment
# def layouts():
#    layouts = CourseLayout.query.all()
#    print(layouts)  # Add this line
#    return render_template('layouts.html', layouts=layouts)

# Route for player management
# @app.route('/players') # not needed at the moment
# def players():
#    players = Player.query.all()
#    return render_template('players.html', players=players)


# Route for detailed scorecard view
@app.route("/scorecard/<int:scorecard_id>")
def scorecard(scorecard_id):
    scorecard = Scorecard.query.get_or_404(scorecard_id)
    if scorecard.total_score is None:
        return "Scorecard not yet completed"
    player = Player.query.get(scorecard.player_id)
    round = Round.query.get(scorecard.round_id)
    course = Course.query.get(round.course_id)
    layout = CourseLayout.query.get(
        round.layout_id
    )  # Get the CourseLayout using the layout_id of the Round
    hole_scores = HoleScore.query.filter_by(scorecard_id=scorecard_id).all()
    par_values = (
        [int(p) for p in layout.par_values.split(",")] if layout.par_values else []
    )
    return render_template(
        "scorecard.html",
        scorecard=scorecard,
        player=player,
        round=round,
        course=course,
        layout=layout,
        hole_scores=hole_scores,
        par_values=par_values,
    )

@app.route("/scorecards_for_player_course_and_layout/player/<player_name>/course/<course_name>/layout/<layout_name>/limit/<int:limit>")
def scorecards_for_player_course_layout(player_name, course_name, layout_name, limit):
    player = Player.query.filter_by(name=player_name).first()
    course = Course.query.filter_by(name=course_name).first()
    layout = CourseLayout.query.filter_by(layout_name=layout_name, course_id=course.id).first()

    scorecards_query = (
        db.session.query(Scorecard, db.func.min(Scorecard.score_difference).label('min_score_difference'))
        .join(Player, Scorecard.player_id == Player.id)
        .join(Round, Scorecard.round_id == Round.id)
        .join(Course, Round.course_id == Course.id)
        .join(CourseLayout, Round.layout_id == CourseLayout.id)
        .filter(Player.name == player_name, Course.name == course_name, CourseLayout.layout_name == layout_name)
        .group_by(Scorecard.id)
        .order_by('min_score_difference')
        .limit(limit)
    )

    scorecards = scorecards_query.all()

    return jsonify(
        [
            {
                "id": scorecard.Scorecard.id,
                "player_id": scorecard.Scorecard.player_id,
                "round_id": scorecard.Scorecard.round_id,
                "total_score": scorecard.Scorecard.total_score,
                "score_difference": scorecard.Scorecard.score_difference,
                "min_score_difference": scorecard.min_score_difference,
                "hole_scores": [
                    hole_score.strokes
                    for hole_score in HoleScore.query.filter_by(
                        scorecard_id=scorecard.Scorecard.id
                    ).all()
                ],
            }
            for scorecard in scorecards
        ]
    )



@app.route("/scorecard_data/<player_name>/<course_name>/<layout_name>/<int:limit>")
def scorecard_data(player_name, course_name, layout_name, limit):
    scorecards_query = (
        db.session.query(Scorecard, db.func.min(Scorecard.score_difference).label('min_score_difference'))
        .join(Player, Scorecard.player_id == Player.id)
        .join(Round, Scorecard.round_id == Round.id)
        .join(Course, Round.course_id == Course.id)
        .join(CourseLayout, Round.layout_id == CourseLayout.id)
        .filter(Player.name == player_name, Course.name == course_name, CourseLayout.layout_name == layout_name)
        .group_by(Scorecard.id)
        .order_by('min_score_difference')
        .limit(limit)
    )

    scorecards = scorecards_query.all()

    return jsonify(
        [
            {
                "id": scorecard.Scorecard.id,
                "player_id": scorecard.Scorecard.player_id,
                "player_name": player_name,
                "course_name": course_name,
                "layout_name": layout_name,
                "round_id": scorecard.Scorecard.round_id,
                "total_score": scorecard.Scorecard.total_score,
                "score_difference": scorecard.Scorecard.score_difference,
                "min_score_difference": scorecard.min_score_difference,
                "hole_scores": [
                    hole_score.strokes
                    for hole_score in HoleScore.query.filter_by(
                        scorecard_id=scorecard.Scorecard.id
                    ).all()
                ],
            }
            for scorecard in scorecards
        ]
    )


@app.route("/index", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        player_name = request.form.get("player_name")
        course_name = request.form.get("course_name")
        layout_name = request.form.get("layout_name")
        scorecard_id = request.form.get("scorecard_id")

        player = Player.query.filter_by(name=player_name).first()
        course = Course.query.filter_by(name=course_name).first()
        layout = CourseLayout.query.filter_by(layout_name=layout_name).first()
        scorecard = db.session.get(Scorecard, scorecard_id)

        if not all([player, course, layout, scorecard]):
            flash("Error: Not all form fields were filled out correctly.")
            return redirect(request.url)

        # Handle form submission (e.g., save data to database)

    players = [player.name for player in Player.query.all()]
    courses = [course.name for course in Course.query.all()]
    layouts = [layout.layout_name for layout in CourseLayout.query.all()]
    scorecards = [scorecard.id for scorecard in Scorecard.query.all()]

    return render_template(
        "index.html",
        players=players,
        courses=courses,
        layouts=layouts,
        scorecards=scorecards,
    )
# create the route for players_for_course_and_layout:
@app.route("/players_for_course_and_layout/<course_name>/<layout_name>")
def players_for_course_and_layout(course_name, layout_name):
    course = Course.query.filter_by(name=course_name).first()
    layout = CourseLayout.query.filter_by(
        layout_name=layout_name, course_id=course.id
    ).first()
    round_ids = (
        db.session.query(Scorecard.round_id)
        .join(Round)
        .filter(Round.course_id == course.id, Round.layout_id == layout.id)
        .distinct()
    )
    player_ids = (
        db.session.query(Scorecard.player_id)
        .filter(Scorecard.round_id.in_(round_ids))
        .distinct()
    )
    players = Player.query.filter(Player.id.in_(player_ids)).all()
    return jsonify([player.name for player in players])


# create the route for courses_for_all_players:
@app.route("/courses_for_all_players/")
def courses_for_all_players():
    courses = (
        db.session.query(Course.name)
        .join(Round)
        .filter(Round.course_id == Course.id)
        .distinct()
        .all()
    )
    return jsonify([course[0] for course in courses])


# the /upload route is not needed at the moment
# @app.route('/upload', methods=['GET', 'POST'])
# def upload_file():
#     if request.method == 'POST':
#         filename = 'UDisc Scorecards.csv'
#         load_data(filename)
#         return redirect(url_for('index'))
#     return render_template('upload.html')


# Modify the main block
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # Check the username and password entered by the user
        # You can add your authentication logic here
        if is_valid_login(request.form["username"], request.form["password"]):
            # If the login is valid, redirect the user to the main page
            return redirect("/index")  # Redirect to the main page
        else:
            # If the login is not valid, show an error message or redirect to the login page again
            return render_template(
                "login.html", error_message="Invalid login credentials"
            )

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # Process registration form data
        username = request.form["username"]
        password = request.form["password"]
        confirm_password = request.form["confirm-password"]
        # Add your registration logic here, e.g., store the user in a database
        # After successful registration, you might redirect the user to the login page
        return redirect("/")
    return render_template("register.html")


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        filename = "UDisc Scorecards.csv"
        load_data(filename)  # Load data when the application starts
    app.run(debug=True)
