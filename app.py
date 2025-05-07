# IMPORT LIBRARY
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import pymysql
from werkzeug.security import generate_password_hash, check_password_hash
from auth import *

# Initialize and configure database
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:minhton23@localhost/CRM'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# define APIs
@app.route('/register', methods=['GET', 'POST'])
def register_route():
    return register()

@app.route('/login', methods=['GET', 'POST'])
def login_route():
    return login()

@app.route('/homepage')
def homepage_route():
    return homepage()

@app.route('/customer-content')
def customer_content_route():
    return customer_content()

@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password_route():
    return reset_password()

@app.route('/bookings')
def bookings_route():
    return bookings()

@app.route('/bookings/save', methods=['POST'])
def save_bookings_route():
    return save_bookings()

@app.route('/bookings/edit/<int:booking_id>', methods=['POST'])
def edit_bookings_route(booking_id):
    return edit_bookings(booking_id)

@app.route('/bookings/delete/<int:booking_id>', methods=['POST'])
def delete_bookings_route(booking_id):
    return delete_booking(booking_id)  # hàm xử lý xóa

@app.route("/customers/save", methods=["POST"])
def save_customers_route():
    return save_customer()

@app.route("/customers/delete/<int:customer_id>", methods=["POST"])
def delete_customers_route(customer_id):
    return delete_customer(customer_id)

@app.route("/payments")
def payments_route():
    return payments()

@app.route("/payments/save", methods=["POST"])
def save_payments_route():
    return save_payments()

@app.route("/payments/delete/<int:payment_id>", methods=["POST"])
def delete_payments_route(payment_id):
    return delete_payments(payment_id)

# run in debug mode
if __name__ == '__main__':
    app.run(debug=True)

