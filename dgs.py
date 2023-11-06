from flask import Flask,flash, abort, request, redirect, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql.elements import ClauseElement
from flask_migrate import Migrate
from datetime import datetime

import pandas as pd
from sqlalchemy import func
from flask import jsonify

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dgs.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)


class MetaData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    last_processed_timestamp = db.Column(db.DateTime, nullable=False, server_default=func.now())

def get_last_processed_timestamp():
    # Fetch the MetaData row from the database. Since there's only one row, we can use first()
    meta_data = MetaData.query.first()

    # If the MetaData row exists, return the last_processed_timestamp
    if meta_data:
        return meta_data.last_processed_timestamp

    # If the MetaData row does not exist, create it with the current timestamp
    else:
        meta_data = MetaData()
        db.session.add(meta_data)
        db.session.commit()
        return meta_data.last_processed_timestamp

def update_last_processed_timestamp(timestamp_str):
    # Convert the timestamp string to a datetime object
    timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H%M')

    # Fetch the MetaData row from the database
    meta_data = MetaData.query.first()

    # Update the last_processed_timestamp field and commit the changes
    meta_data.last_processed_timestamp = timestamp
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
            params = dict((k, v) for k, v in kwargs.items() if not isinstance(v, ClauseElement))
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
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))
    layout_name = db.Column(db.String(64))
    hole_count = db.Column(db.Integer)
    par_values = db.Column(db.String(128))
    course = db.relationship('Course', backref=db.backref('layouts', lazy=True))

# Player represents a disc golf player. It has a unique name.
class Player(BaseModel):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)

# Round represents a round of disc golf. It is associated with a Course and a CourseLayout. It has a unique date.
class Round(BaseModel):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))
    layout_id = db.Column(db.Integer, db.ForeignKey('course_layout.id'))
    date = db.Column(db.Date)

# Scorecard represents a player's scorecard for a round. It is associated with a Player and a Round. It has various attributes, such as the total score and the total number of throws.
class Scorecard(BaseModel):
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'))
    round_id = db.Column(db.Integer, db.ForeignKey('round.id'))
    total_score = db.Column(db.Integer)
    score_difference = db.Column(db.Integer)
    total_throws = db.Column(db.Integer)
# HoleScore represents a player's score for a specific hole. It is associated with a Scorecard. It has the hole number and the number of strokes.
class HoleScore(BaseModel):
    id = db.Column(db.Integer, primary_key=True)
    scorecard_id = db.Column(db.Integer, db.ForeignKey('scorecard.id'))
    hole_number = db.Column(db.Integer)
    strokes = db.Column(db.Integer)

# Data upload route (not needed at the moment)

#@app.route('/upload', methods=['GET', 'POST'])
#def upload_file():
#   if request.method == 'POST':
#        filename = 'UDisc Scorecards.csv'
#        load_data(filename)
#        return redirect(url_for('index'))
#    return render_template('upload.html')

def load_data(filename):
    try:
        df = pd.read_csv(filename)
        df['Kaikki'] = df['Kaikki'].fillna(0)
        last_processed_timestamp = get_last_processed_timestamp()
        for index, row in df.iterrows():
            row_timestamp = datetime.strptime(row['Päivämäärä'], '%Y-%m-%d %H%M')
            if row_timestamp > last_processed_timestamp:    
                process_row(row)
        db.session.commit()
        print("Committed changes to the database")
        update_last_processed_timestamp(df['Päivämäärä'].max())  # Update the last processed timestamp
    except Exception as e:
        print("Error loading data:", str(e))
        db.session.rollback()
        player_count = db.session.query(func.count(Player.id)).scalar()
        print(f"Loaded {player_count} players")

def process_row(row):
    # Create or retrieve the player
    player_name = row['PlayerName'].strip()
    player, created = Player.get_or_create(name=player_name)

    # Create or retrieve the course
    course_name = row['CourseName']
    course, created = Course.get_or_create(name=course_name)

    # Create or retrieve the layout
    layout_name = row['LayoutName']
    layout, created = CourseLayout.get_or_create(course_id=course.id, layout_name=layout_name)
    if created:
        hole_count = sum(pd.notna(row[f'Hole{i}']) for i in range(1, 25))
        layout.hole_count = hole_count
        db.session.add(layout)

        if player_name == 'Par':
            par_values = [int(row[f'Hole{i}']) if pd.notna(row[f'Hole{i}']) else 0 for i in range(1, 25)]
            layout.par_values = ','.join(map(str, par_values))

    # Create the round
    date_string = row['Päivämäärä']
    date_object = datetime.strptime(date_string, '%Y-%m-%d %H%M').date()  # Adjust the format string as needed
    round, created = Round.get_or_create(course_id=course.id, layout_id=layout.id, date=date_object)

    # Create the scorecard and hole scores
    if player_name != 'Par':
        total_throws = int(row['Kaikki']) if pd.notna(row['Kaikki']) else None
        total_score = int(row['Kaikki']) if pd.notna(row['Kaikki']) else None
        score_difference = int(row['+/-']) if pd.notna(row['+/-']) else 0
        scorecard, created = Scorecard.get_or_create(player_id=player.id, round_id=round.id, total_score=total_score, score_difference=score_difference, total_throws=total_throws)

        for i in range(1, 25):
            if pd.notna(row[f'Hole{i}']):
                hole_score, created = HoleScore.get_or_create(scorecard_id=scorecard.id, hole_number=i, strokes=int(row[f'Hole{i}']))

    db.session.commit()

# Route to check if coursedata is present in the database (not needed at the moment)
#@app.route('/check_data', methods=['GET'])
#def check_data():
#    course_count = db.session.query(func.count(Course.id)).scalar()
#    layout_count = db.session.query(func.count(CourseLayout.id)).scalar()
#
#    if course_count > 0 and layout_count > 0:
#        return 'Data is present in the database'
#    else:
#        return 'No data found in the database'

# Additional routes for your application (layouts, detailed scorecard view, etc.)

# Route to display top scores for each course and layout (not needed at the moment)
@app.route('/top_scores')
def top_scores():
    top_scores = []
    courses = Course.query.all()
    for course in courses:
        layouts = CourseLayout.query.filter_by(course_id=course.id).all()
        for layout in layouts:
            scores = db.session.query(Scorecard.total_score, Player.name).join(Player).filter(Scorecard.round_id != None, Scorecard.total_score != None, Scorecard.total_throws != None, Scorecard.score_difference != None, Scorecard.score_difference >= 0, Scorecard.score_difference <= 2, Scorecard.player_id == Player.id, Scorecard.round_id == Round.id, Round.course_id == course.id, Round.layout_id == layout.id).order_by(Scorecard.total_score).limit(10).all()
            top_scores.append({'course': course.name, 'layout': layout.layout_name, 'scores': [{'name': score[1], 'score': score[0]} for score in scores]})
    return jsonify(top_scores)


@app.route('/layouts_for_course/<course_name>')
def layouts_for_course(course_name):
    course = Course.query.filter_by(name=course_name).first()
    if course is None:
        abort(404, description="Course not found")
    layouts = CourseLayout.query.filter_by(course_id=course.id).all()
    return jsonify([layout.layout_name for layout in layouts])

@app.route('/courses_for_player/<player_name>')
def courses_for_player(player_name):
    player = Player.query.filter_by(name=player_name).first()
    if player is None:
        abort(404, description="Player not found")
    round_ids = db.session.query(Scorecard.round_id).filter_by(player_id=player.id).distinct()
    course_ids = db.session.query(Round.course_id).filter(Round.id.in_(round_ids)).distinct()
    courses = Course.query.filter(Course.id.in_(course_ids)).all()
    return jsonify([course.name for course in courses])

# Route for course management (not needed at the moment)
#@app.route('/courses')
#def courses():
#    courses = Course.query.all()
#    return render_template('courses.html', courses=courses)


# Route for layout management

#@app.route('/layouts')  # not needed at the moment
#def layouts():
#    layouts = CourseLayout.query.all()
#    print(layouts)  # Add this line
#    return render_template('layouts.html', layouts=layouts)

# Route for player management
#@app.route('/players') # not needed at the moment
#def players():
#    players = Player.query.all()
#    return render_template('players.html', players=players)

# Route for detailed scorecard view
@app.route('/scorecard/<int:scorecard_id>')
def scorecard(scorecard_id):
    scorecard = Scorecard.query.get_or_404(scorecard_id)
    if scorecard.total_score is None:
        return 'Scorecard not yet completed'
    player = Player.query.get(scorecard.player_id)
    round = Round.query.get(scorecard.round_id)
    course = Course.query.get(round.course_id)
    layout = CourseLayout.query.get(round.layout_id)  # Get the CourseLayout using the layout_id of the Round
    hole_scores = HoleScore.query.filter_by(scorecard_id=scorecard_id).all()
    par_values = [int(p) for p in layout.par_values.split(',')] if layout.par_values else []
    return render_template('scorecard.html', scorecard=scorecard, player=player, round=round, course=course, layout=layout, hole_scores=hole_scores, par_values=par_values)

    
@app.route('/scorecards_for_player_course_layout')
def scorecards_for_player_course_layout():
    player_name = request.args.get('player_name')
    course_name = request.args.get('course_name')
    layout_name = request.args.get('layout_name')

    player = Player.query.filter_by(name=player_name).first()
    course = Course.query.filter_by(name=course_name).first()
    layout = CourseLayout.query.filter_by(layout_name=layout_name, course_id=course.id).first()

    scorecards = Scorecard.query.filter_by(player_id=player.id).join(Round).filter(Round.course_id==course.id, Round.layout_id==layout.id).all()

    return jsonify([{
        'id': scorecard.id,
        'player_id': scorecard.player_id,
        'round_id': scorecard.round_id,
        'total_score': scorecard.total_score,
        'score_difference': scorecard.score_difference,
        'total_throws': scorecard.total_throws,
        'hole_scores': [hole_score.strokes for hole_score in HoleScore.query.filter_by(scorecard_id=scorecard.id).all()],
    } for scorecard in scorecards])

@app.route('/scorecard_data/<player_name>/<course_name>/<layout_name>')
def scorecard_data(player_name, course_name, layout_name):
    print(f'course_name: {course_name}')

    player = Player.query.filter_by(name=player_name).first()
    course = Course.query.filter_by(name=course_name).first()

    if course is None:
        return jsonify({
            'error': 'No course found with the specified name'
        }), 404

    layout = CourseLayout.query.filter_by(
        layout_name=layout_name, course_id=course.id).first()
    print(f'course: {course}')

    scorecards = Scorecard.query.filter_by(
        player_id=player.id
    ).join(Round).filter(
        Round.course_id == course.id,
        Round.layout_id == layout.id
    ).all()
#here is where we print the scorecard data
    return jsonify([{  
        'id': scorecard.id,
        'player_id': scorecard.player_id,
        'player_name': player.name,
        'course_name': course.name,
        'layout_name': layout.layout_name,
        'round_id': scorecard.round_id,
        'total_score': scorecard.total_score,
        'score_difference': scorecard.score_difference,
        'total_throws': scorecard.total_throws,
        'hole_scores': [
            hole_score.strokes for hole_score in HoleScore.query
            .filter_by(scorecard_id=scorecard.id)
            .all()
        ]
    } for scorecard in scorecards])
          

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        player_name = request.form.get('player_name')
        course_name = request.form.get('course_name')
        layout_name = request.form.get('layout_name')
        scorecard_id = request.form.get('scorecard_id')

        player = Player.query.filter_by(name=player_name).first()
        course = Course.query.filter_by(name=course_name).first()
        layout = CourseLayout.query.filter_by(layout_name=layout_name).first()
        scorecard = db.session.get(Scorecard, scorecard_id)

        if not all([player, course, layout, scorecard]):
            flash('Error: Not all form fields were filled out correctly.')
            return redirect(request.url)

        # Handle form submission (e.g., save data to database)

    players = [player.name for player in Player.query.all()]
    courses = [course.name for course in Course.query.all()]
    layouts = [layout.layout_name for layout in CourseLayout.query.all()]
    scorecards = [scorecard.id for scorecard in Scorecard.query.all()]

    return render_template('index.html', players=players, courses=courses, layouts=layouts, scorecards=scorecards)

# the /upload route is not needed at the moment
# @app.route('/upload', methods=['GET', 'POST'])
# def upload_file():
#     if request.method == 'POST':
#         filename = 'UDisc Scorecards.csv'
#         load_data(filename)
#         return redirect(url_for('index'))
#     return render_template('upload.html')

# Modify the main block


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        filename = 'UDisc Scorecards.csv'
        load_data(filename)  # Load data when the application starts
    app.run(debug=True)