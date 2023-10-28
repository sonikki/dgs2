from flask import Flask, render_template, request
import pandas as pd

app = Flask(__name__)

# Read in the CSV file 'UDisc Scorecards.csv' into a pandas DataFrame called 'df'
df = pd.read_csv('UDisc Scorecards.csv')

# Replace all null values in the DataFrame with 0 and convert the 'Päivämäärä' column to a datetime object
df = df.where(pd.notnull(df), 0)
df['Päivämääärä'] = pd.to_datetime(df['Päivämäärä'])
df['tulos'] = df['+/-']

@app.route('/', methods=['GET', 'POST'])
def index():
    # Get a list of all unique player and course names in the DataFrame
    player_names = df.loc[df['PlayerName'] != 'Par', 'PlayerName'].unique().tolist()
    player_names.insert(0, 'All Players') # Add an option for selecting all players
    course_names = df.loc[df['CourseName'].notnull(), 'CourseName'].unique().tolist()

    # If the user has submitted the form, retrieve the selected player and course names
    if request.method == 'POST':
        selected_player = request.form['player']
        selected_course = request.form['course']

        # Filter the DataFrame to only include rounds played by the selected player on the selected course
        if selected_player == 'All Players':
            # If the user selected "All Players," only filter by the selected course
            filtered_df = df.loc[(df['CourseName'] == selected_course) & (df['PlayerName'] != 'Par')]
        else:
            # Filter the DataFrame as usual
            filtered_df = df.loc[(df['PlayerName'] == selected_player) & (df['CourseName'] == selected_course) & (df['PlayerName'] != 'Par')]

        # Get the top 10 scores for the selected player on the selected course
        top10_scores = filtered_df.nsmallest(10, 'tulos')

        # Render the template with the selected player and course names and the top 10 scores
        return render_template('index.html', player_names=player_names, course_names=course_names, selected_player=selected_player, selected_course=selected_course, top10_scores=top10_scores)

    # If the user has not submitted the form, pass an empty DataFrame to the 'top10_scores' variable
    else:
        top10_scores = pd.DataFrame()
        return render_template('index.html', player_names=player_names, course_names=course_names, top10_scores=top10_scores)

if __name__ == '__main__':
    app.run(debug=True)