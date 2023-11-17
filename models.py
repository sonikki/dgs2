from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func, ClauseElement
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey 
from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base

db = SQLAlchemy()

Base = declarative_base()
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


#%%
# Define database models


# BaseModel is an abstract base class for all other models. It provides common methods that can be used by all models.
class BaseModel(db.Model):
    __abstract__ = True

    @classmethod
    def get_or_create(cls, defaults=None, commit=True, **kwargs):
        try:
            instance = db.session.query(cls).filter_by(**kwargs).first()
            if instance:
                return instance, False
            else:
                params = {k: v for k, v in kwargs.items() if not isinstance(v, ClauseElement)}
                params.update(defaults or {})
                instance = cls(**params)
                db.session.add(instance)
                if commit:
                    db.session.commit()  # Commit here to get the auto-generated IDs
                return instance, True
        except Exception as e:
            print("Error in get_or_create:", str(e))
            db.session.rollback()
            raise e



class RowProcessed(Base):
    __tablename__ = 'row_processed'

    id = Column(Integer, primary_key=True)
    player_name = Column(String)
    date = Column(Date)



class Player(BaseModel):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)

class Course(BaseModel):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)

class Layout(BaseModel):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)

class Round(BaseModel):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    layout_id = db.Column(db.Integer, db.ForeignKey('layout.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False)

    # Add relationships to Course and Layout
    course = db.relationship('Course', foreign_keys=[course_id], backref=db.backref('rounds', lazy=True))
    layout = db.relationship('Layout', foreign_keys=[layout_id], backref=db.backref('rounds', lazy=True))


class Scorecard(BaseModel):
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=False)
    round_id = db.Column(db.Integer, db.ForeignKey('round.id'), nullable=False)
    total_score = db.Column(db.Integer, nullable=False)
    score_difference = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DateTime, nullable=False)

class HoleScore(BaseModel):
    id = db.Column(db.Integer, primary_key=True)
    scorecard_id = db.Column(db.Integer, db.ForeignKey('scorecard.id'), nullable=False)
    hole_number = db.Column(db.Integer, nullable=False)
    strokes = db.Column(db.Integer, nullable=False)