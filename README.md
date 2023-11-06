# Disc Golf Statistics - Score tracker

This is a web application for tracking disc golf scores. It allows users to upload Udisc exportable CSV files with score data, which is then stored in a database and can be queried through various endpoints.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

- Python 3.6 or later
- Flask
- SQLAlchemy
- pandas

You can install these packages using pip:

```bash
pip install flask sqlalchemy pandas


## Usage

The application provides the following endpoints:

- `/upload`: This endpoint allows you to upload a CSV file with score data. The data is then loaded into the database.

- `/check_data`: This endpoint returns the number of players and courses in the database.

