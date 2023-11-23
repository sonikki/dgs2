import pandas as pd
from datetime import datetime
from models import db, MetaData, Player, Course, Layout, Round, Scorecard, HoleScore
from models import get_last_processed_timestamp, update_last_processed_timestamp




def load_data(filename):
    try:
        meta_data = MetaData.query.first()
        if meta_data is None:
            meta_data = MetaData(last_processed_timestamp=datetime.min)
            db.session.add(meta_data)

        df = pd.read_csv(filename)
        print(df['Kaikki'].unique())

        last_processed_timestamp = get_last_processed_timestamp() or datetime.min

        # Filter rows based on timestamp
        df['Päivämäärä'] = pd.to_datetime(df['Päivämäärä'], format='%Y-%m-%d %H%M')
        df = df[df['Päivämäärä'].apply(lambda x: x.to_pydatetime() >= last_processed_timestamp)]
        total_rows = len(df)
        # Process the filtered rows
        for _, row in df.iterrows():
            process_row(row)
            print(f'\rProcessed {_}/{total_rows} rows ({_/total_rows*100:.2f}%)', end='')

        # Update the last processed timestamp
        if not df.empty:
            max_processed_timestamp = df['Päivämäärä'].max().to_pydatetime()
            update_last_processed_timestamp(max_processed_timestamp)

        # Print counters
        print(f"Processed {len(df)} rows")

    except Exception as e:
        print("Error loading data:", str(e))
        db.session.rollback()





#%%


def get_par_for_hole(layout_id, hole_number):
    layout = Layout.query.get(layout_id)
    if layout:
        par_values = layout.get_par_values()
        if hole_number <= len(par_values):
            return par_values[hole_number - 1]
    return None



# counter for rows processed for debugging purposes
def process_data(data):
    total_rows = len(data)
    for i, row in enumerate(data, start=1):
        process_row(row)
        print(f'\rProcessed {i}/{total_rows} rows ({i/total_rows*100:.2f}%)', end='')


def process_row(row):
    try:
        player_name = row['PlayerName'].strip()
        player, _ = Player.get_or_create(name=player_name)

        course_name = row['CourseName']
        course, _ = Course.get_or_create(name=course_name)

        layout_name = row['LayoutName']
        layout, _ = Layout.get_or_create(
            course_id=course.id,
            name=layout_name
        )

        date_object = row['Päivämäärä'].to_pydatetime()

        # Fill in the "Kaikki" column for the 'Par' player
        if player_name == 'Par':
            row['Kaikki'] = 0  # Set a default value for the 'Par' player
            # Update par values in the Layout table
            par_values = [int(row[f'Hole{hole_number}']) for hole_number in range(1, 25) if pd.notna(row[f'Hole{hole_number}'])]
            layout.set_par_values(par_values)
            db.session.commit()

        total_score = row['Kaikki']
        score_difference = row['+/-']
        if pd.isna(score_difference):
            score_difference = 0

        # Create or get the round object
        round_obj, _ = Round.get_or_create(
            course_id=course.id,
            layout_id=layout.id,
            date=date_object
        )

        # Get or create the scorecard for the player and the round
        scorecard, _ = Scorecard.get_or_create(
            player_id=player.id,
            round_id=round_obj.id,
            layout_id=layout.id,  
            total_score=total_score,
            score_difference=score_difference,
            date=date_object
        )

        # Using DataFrame operations to iterate over holes
        for hole_number in range(1, 25):
            if pd.notna(row[f'Hole{hole_number}']):
                strokes = int(row[f'Hole{hole_number}'])
                # Retrieve par value for the hole
                par = get_par_for_hole(layout.id, hole_number)
                # Set a default value for par if it is None
                par = par if par is not None else 0
                # Ensure the HoleScore is associated with the correct Scorecard
                hole_score, _ = HoleScore.get_or_create(
                    scorecard_id=scorecard.id,
                    hole_number=hole_number,
                      strokes=strokes                    
                )


    except Exception as e:
        print("Error processing row:", str(e))
        raise e
