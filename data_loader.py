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

        # Process the filtered rows
        for _, row in df.iterrows():
            process_row(row)

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
            total_score=total_score,
            score_difference=score_difference,
            date=date_object
        )

        # Using DataFrame operations to iterate over holes
        for hole_number in range(1, 25):
            if pd.notna(row[f'Hole{hole_number}']):
                strokes = int(row[f'Hole{hole_number}'])
                # Ensure the HoleScore is associated with the correct Scorecard
                hole_score, _ = HoleScore.get_or_create(
                    scorecard_id=scorecard.id,
                    hole_number=hole_number,
                    strokes=strokes
                )
                # print(f"Hole {hole_number}: {strokes}")

    except Exception as e:
        print("Error processing row:", str(e))
        raise e

