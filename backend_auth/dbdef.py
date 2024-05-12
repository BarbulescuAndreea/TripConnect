from dataclasses import dataclass
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

@dataclass
class Flight(db.Model):
    __tablename__ = "Flight"

    flight_id: int
    number: int
    departure_time: datetime
    arrival_time: datetime
    company_name: str

    flight_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    number = db.Column(db.Integer, nullable=False)
    departure_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    arrival_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    company_name = db.Column(db.String(40), nullable=False)


@dataclass
class Users(db.Model):
    __tablename__ = "Users"

    user_id: int
    name: str
    password: str
    registration_date: datetime
    email: str

    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(300), nullable=False)
    registration_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    email = db.Column(db.String(50), nullable=False, unique=True)

@dataclass
class Transfers(db.Model):
    __tablename__ = "Transfers"

    transfer_id: int
    type: str
    source: str
    destination: str
    flight_id: int

    transfer_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    type = db.Column(db.String(30), nullable=False)
    source = db.Column(db.String(100), nullable=False)
    destination = db.Column(db.String(100), nullable=False)
    flight_id = db.Column(db.Integer, db.ForeignKey("Flight.flight_id"), nullable=False)

@dataclass
class Bookings(db.Model):
    __tablename__ = "Bookings"

    booking_id: int
    flight_id: int
    user_id: int
    booking_date: datetime
    payment_status: str


    booking_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    flight_id = db.Column(db.Integer, db.ForeignKey("Flight.flight_id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("Users.user_id", ondelete='CASCADE'), nullable=False)
    booking_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    payment_status = db.Column(db.String(50), nullable=False)

@dataclass
class Reviews(db.Model):
    __tablename__ = "Reviews"

    review_id: int
    flight_id: int
    user_id: int
    rating: int
    comment: str

    review_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    flight_id = db.Column(db.Integer, db.ForeignKey("Flight.flight_id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("Users.user_id", ondelete='CASCADE'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=True)



