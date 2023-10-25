from flask import Flask, render_template, request
import pandas as pd

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Load the data from the CSV file
df = pd.read_csv('data.csv')
print(df.head())

# Define a function to get the top scores for a given course and number of holes
def get_top_scores(course_name, num_holes):
    course_df = df[df['CourseName'] == course_name]
    print(course_df.head())
    if course_df.empty:
        return None
    hole_columns = [col for col in course_df.columns if col.startswith('Hole')]
    max_holes = len(hole_columns)
    if max_holes < num_holes:
        return None
    selected_columns = ['PlayerName', 'Total'] + hole_columns[:num_holes]
    top_scores = course_df.sort_values(by=['+/-'], ascending=False)[selected_columns]
    top_scores = top_scores[top_scores['PlayerName'] != 'Par'].head(10)
    player_names = top_scores['PlayerName'].tolist()
    total_scores = top_scores['Total'].tolist()
    num_players = len(player_names)
    return {'top_scores': top_scores, 'player_names': player_names, 'total_scores': total_scores, 'num_players': num_players}

# Define a route for getting the top scores for a given course and number of holes
@app.route('/top-scores', methods=['GET'])
def top_scores():
    print("Calling top_scores() function")
    course_name = request.args.get('course')
    num_holes = request.args.get('num_holes')
    if not course_name or not num_holes:
        return {'error': 'Invalid request'}
    num_holes = int(num_holes)
    result = get_top_scores(course_name, num_holes)
    if not result:
        return {'error': 'Invalid course or number of holes'}
    result['course_name'] = course_name
    return result

@app.route('/', methods=['GET', 'POST'])
def index():
    print("Calling index() function")
    # If the request method is POST, update the selected columns and render the HTML template with the updated columns
    if request.method == 'POST':
        selected_columns = request.form.getlist('columns')
        return render_template('index.html', selected_columns=selected_columns)

    # If the request method is GET and a course has been selected, render the HTML template with the top scores for the selected course
    course_name = request.args.get('course')
    if course_name:
        course_df = df[df['CourseName'] == course_name]
        if course_df.empty:
            return render_template('error.html', message='The selected course has no scores.')
        max_holes = course_df['Hole'].max() if 'Hole' in course_df.columns else 0
        if max_holes < 9:
            return render_template('error.html', message='The selected course has less than 9 holes.')
        elif max_holes > 24:
            return render_template('error.html', message='The selected course has more than 24 holes.')
        else:
            course_df = course_df[course_df['Hole'] <= max_holes]
            selected_columns = ['PlayerName', 'Total'] + [f'Hole {i}' for i in range(1, max_holes+1)]
            top_scores = course_df.sort_values(by=['+/-'], ascending=False)[selected_columns]
            top_scores = top_scores[top_scores['PlayerName'] != 'Par'].head(10)
            player_names = top_scores['PlayerName'].tolist()
            total_scores = top_scores['Total'].tolist()
            num_players = len(player_names)
            return render_template('index.html', top_scores=top_scores, course_name=course_name, courses=df['CourseName'].unique(), player_names=player_names, total_scores=total_scores, num_players=num_players)

    # If the request method is GET and no course has been selected, render the HTML template with a list of courses to choose from
    else:
        top_scores = pd.DataFrame()
        return render_template('index.html', top_scores=top_scores, courses=df['CourseName'].unique())

@app.route('/select', methods=['POST'])
def select():
    print("Calling select() function")
    selected_course = request.form['course']
    if 'num_holes' in request.form:
        num_holes = int(request.form['num_holes'])
    else:
        num_holes = 18
    course_df = df[df['CourseName'] == selected_course]
    if course_df.empty:
        return render_template('error.html', message='Invalid course or number of holes')
    max_holes = course_df['Hole'].max() if 'Hole' in course_df.columns else 0
    if max_holes < num_holes:
        return render_template('error.html', message='Invalid course or number of holes')
    selected_columns = ['PlayerName', 'Total'] + [f'Hole {i}' for i in range(1, num_holes+1)]
    top_scores = course_df[course_df['Hole'] <= max_holes].sort_values(by=['+/-'], ascending=False)[selected_columns]
    top_scores = top_scores[top_scores['PlayerName'] != 'Par'].head(10)
    player_names = top_scores['PlayerName'].tolist()
    total_scores = top_scores['Total'].tolist()
    num_players = len(player_names)
    return render_template('index.html', top_scores=top_scores, course_name=selected_course, courses=df['CourseName'].unique(), player_names=player_names, total_scores=total_scores, num_players=num_players)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    print("Calling upload() function")
    if request.method == 'POST':
        file = request.files['file']
        new_data = pd.read_csv(file)
        global df
        df = pd.concat([df, new_data]).drop_duplicates()
        top_scores = get_top_scores(df['CourseName'].unique()[0], 18)
        if not top_scores:
            return render_template('error.html', message='The selected course has no scores.')
        return render_template('index.html', top_scores=top_scores['top_scores'], course_name=top_scores['course_name'], courses=df['CourseName'].unique())

    return render_template('upload.html')

if __name__ == '__main__':
    app.run(debug=True)