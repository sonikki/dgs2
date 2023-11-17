#%%
from flask import Flask, flash, abort, request, redirect, jsonify, render_template
from models import db, MetaData, Player, Course, Layout, Round, Scorecard, HoleScore
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime
from sqlalchemy.orm.exc import NoResultFound
import pandas as pd
from sqlalchemy import func
from flask import jsonify
from data_loader import load_data

def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///dgs.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    return app

app = create_app()
migrate = Migrate(app, db)



def is_valid_login(username, password):
    # For now, just return True to allow access but can be customized in future
    return True


#%%

@app.route('/hole_scores/<int:scorecard_id>')
def hole_scores(scorecard_id):
    scorecard = Scorecard.query.get_or_404(scorecard_id)

    hole_scores = db.session.query(
        HoleScore.hole_number,
        HoleScore.strokes,
        Layout.name,
        Course.name
    ).select_from(HoleScore).join(
        Scorecard,
        Scorecard.id == HoleScore.scorecard_id
    ).join(
        Round,
        Round.id == Scorecard.round_id
    ).join(
        Layout,
        Layout.id == Round.layout_id
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
    layouts = Layout.query.filter_by(course_id=course.id).all()
    return jsonify([layout.name for layout in layouts])


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


# Route for detailed scorecard view
@app.route("/scorecard/<int:scorecard_id>")
def scorecard(scorecard_id):
    scorecard = Scorecard.query.get_or_404(scorecard_id)
    if scorecard.total_score is None:
        return "Scorecard not yet completed"
    player = Player.query.get(scorecard.player_id)
    round = Round.query.get(scorecard.round_id)
    course = Course.query.get(round.course_id)
    layout = Layout.query.get(
        round.layout_id
    )  # Get the Layout using the layout_id of the Round
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
@app.route("/scorecard_data/<player_name>/<course_name>/<layout_name>/<int:limit>")
def scorecard_data(player_name, course_name, layout_name, limit):
    player = Player.query.filter_by(name=player_name).first()
    course = Course.query.filter_by(name=course_name).first()
    layout = Layout.query.filter_by(name=layout_name, course_id=course.id).first()

    if player is None or layout is None:
        abort(404, description="Player or Layout not found")

    print(f"Player: {player_name}), Course: {course_name}, Layout: {layout_name}")

    scorecards_query = (
        db.session.query(
            Scorecard.id,
            Scorecard.player_id,
            Scorecard.round_id,
            Scorecard.total_score,
            Scorecard.score_difference,
            db.func.min(Scorecard.score_difference).label('min_score_difference'))
        .join(Player, Scorecard.player_id == player.id)
        .join(Round, Scorecard.round_id == Round.id)
        .join(Course, Round.course_id == Course.id)
        .join(Layout, Round.layout_id == layout.id)
        .filter(Player.name == player_name, Course.name == course_name, Layout.name == layout_name)
        .group_by(Scorecard.id)
        .order_by(db.func.min(Scorecard.score_difference))
        .limit(limit)
    )

    # Remove the try-except block temporarily to get a detailed error message
    # try:
    scorecards = scorecards_query.all()
    print(f"SQL Query: {scorecards_query}")
    # except Exception as e:
    #     # print the error message
    #     print("Error:", str(e))
    #     return jsonify({"error": str(e)})

    return jsonify(
        [
            {
                "id": scorecard.id,
                "player_id": scorecard.player_id,
                "round_id": scorecard.round_id,
                "total_score": scorecard.total_score,
                "score_difference": scorecard.score_difference,
                "min_score_difference": scorecard.min_score_difference,
                "hole_scores": [
                    hole_score.strokes
                    for hole_score in HoleScore.query.filter_by(
                        scorecard_id=scorecard.id
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
        layout = Layout.query.filter_by(name=layout_name).first()
        scorecard = db.session.get(Scorecard, scorecard_id)

        if not all([player, course, layout, scorecard]):
            flash("Error: Not all form fields were filled out correctly.")
            return redirect(request.url)

        # Handle form submission (e.g., save data to database)

    players = [player.name for player in Player.query.all()]
    courses = [course.name for course in Course.query.all()]
    layouts = [layout.name for layout in Layout.query.all()]
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
    layout = Layout.query.filter_by(
        name=layout_name, course_id=course.id
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
