from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
import pandas as pd

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///scorecards.db'
db = SQLAlchemy(app)

class Scorecard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player_name = db.Column(db.String(50))
    course_name = db.Column(db.String(50))
    date = db.Column(db.DateTime)
    score = db.Column(db.Integer)
    kaikki = db.Column(db.Integer)

    def __init__(self, player_name, course_name, date, score, kaikki):
        self.player_name = player_name
        self.course_name = course_name
        self.date = date
        self.score = score
        self.kaikki = kaikki

# Load and process the data
def load_data():
    if Scorecard.query.first() is None:
        try:
            df = pd.read_csv('UDisc Scorecards.csv')

            # Convert 'Päivämäärä' column to datetime
            df['Päivämäärä'] = pd.to_datetime(df['Päivämäärä'])

            for _, row in df.iterrows():
                scorecard = Scorecard(row['PlayerName'], row['CourseName'], row['Päivämäärä'], row['+/-'], row['Kaikki'])
                db.session.add(scorecard)

            db.session.commit()
        except FileNotFoundError:
            print("Error: File not found")

def remove_duplicates():
    duplicates = db.session.query(Scorecard.player_name, Scorecard.course_name, Scorecard.date, Scorecard.score).group_by(Scorecard.player_name, Scorecard.course_name, Scorecard.date, Scorecard.score).having(db.func.count() > 1).all()
    for duplicate in duplicates:
        dup_records = Scorecard.query.filter_by(player_name=duplicate.player_name, course_name=duplicate.course_name, date=duplicate.date, score=duplicate.score).all()
        for record in dup_records[1:]:
            db.session.delete(record)
    db.session.commit()

with app.app_context():
    db.create_all()
    load_data()
    remove_duplicates()

@app.route('/', methods=['GET', 'POST'])
def index():
    player_names = Scorecard.query.with_entities(Scorecard.player_name).distinct().all()
    course_names = Scorecard.query.with_entities(Scorecard.course_name).distinct().all()

    top10_scores = []
    message = ''

    if request.method == 'POST':
        selected_player = request.form['player']
        selected_course = request.form['course']

        if selected_player == 'All Players':
            top10_scores = Scorecard.query.filter(Scorecard.score.isnot(None), Scorecard.course_name == selected_course).order_by(Scorecard.score).limit(10).all()
        else:
            top10_scores = Scorecard.query.filter(Scorecard.score.isnot(None), Scorecard.player_name == selected_player, Scorecard.course_name == selected_course).order_by(Scorecard.score).limit(10).all()

        # Convert top10_scores to a list of dictionaries
        top10_scores = [scorecard.__dict__ for scorecard in top10_scores]
        if not top10_scores:
            message = 'No scores found for ' + selected_player + ' at ' + selected_course

    return render_template('index.html', player_names=player_names, course_names=course_names, top10_scores=top10_scores, message=message)

if __name__ == '__main__':
    app.run(debug=True)