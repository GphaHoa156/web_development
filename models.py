from flask_sqlalchemy import SQLAlchemy
from datetime import date
from sqlalchemy import DECIMAL

db = SQLAlchemy()

class Users(db.Model):
    __tablename__ = 'users_login'  
    id = db.Column(db.Integer, primary_key=True)
    employee_code = db.Column(db.String(50), unique=True, nullable=False)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    personal_password = db.Column('self_password',db.String(50), unique=True, nullable=False)

class Customers(db.Model):
    __tablename__ = 'Customers'
    customer_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    customer_name = db.Column(db.String(255), nullable=False)
    dob = db.Column(db.Date, nullable=False)
    nationality = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    passport_number = db.Column(db.String(25), nullable=False)
    personal_phone = db.Column(db.String(20), nullable=False)

class Bookings(db.Model):
    __tablename__ = 'Bookings'
    booking_id = db.Column(db.Integer, primary_key=True, autoincrement = True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer_id'))
    service_id = db.Column(db.String(50), nullable = False)
    checkin_date = db.Column(db.Date, nullable = False)
    checkout_date = db.Column(db.Date, nullable = False)
    booking_status = db.Column(db.String(25), nullable = False)
    date_created = db.Column(db.Date, default = date.today)

class Payment(db.Model):
    __tablename__ = 'Payment'
    payment_id = db.Column(db.Integer, primary_key=True, autoincrement = True)
    booking_id = db.Column(db.Integer, nullable = False)
    amount = db.Column(DECIMAL(10,2), nullable = False)
    payment_method = db.Column(db.String(50), nullable = False)
    payment_date = db.Column(db.Date, nullable = False)