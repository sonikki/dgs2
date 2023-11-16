import pandas as pd

def clean_data(input_filename, output_filename='cleaned_data.csv'):
    try:
        # Load the CSV file into a DataFrame
        df = pd.read_csv(input_filename)

        # Handle missing values (fill with zeros)
        df.fillna(0, inplace=True)

        # Convert timestamp to datetime format
        df['Päivämäärä'] = pd.to_datetime(df['Päivämäärä'], format='%Y-%m-%d %H%M')

        # Add a new column for the "+/-" values
        df['+/-'] = df['+/-'].astype(int)

        # Create a list of Hole columns
        hole_columns = [col for col in df.columns if col.startswith('Hole')]

        # Sum Hole scores for each row and add a new column for "Kaikki"
        df['Kaikki'] = df[hole_columns].sum(axis=1)

        # Save the cleaned DataFrame to a new CSV file
        df.to_csv(output_filename, index=False)

        print(f"Data cleaned and saved to {output_filename}")

    except Exception as e:
        print("Error cleaning data:", str(e))

# Usage example
if __name__ == "__main__":
    input_filename = 'Udisc Scorecards.csv'  # Replace with your actual filename
    clean_data(input_filename)
