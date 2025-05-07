from flask import request, render_template, redirect, url_for
from models import *
import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots
from collections import Counter
from sqlalchemy import extract, func
import pandas as pd

def register():
    if request.method == 'POST':    
        username = request.form['username']
        password = request.form['password']
        employee_code = request.form['employee_code']
        personal_password = request.form['personal_password']
        existing_user = Users.query.filter_by(username=username).first()
        if existing_user:
            return render_template('pre_login/register.html', 
                                   message="Это имя пользователь уже существует!")
        new_user = Users(employee_code = employee_code,
                        username=username, 
                        password=password,
                        personal_password = personal_password)
        db.session.add(new_user)
        db.session.commit()
        return render_template('pre_login/register.html', 
                               message = "Поздравления! Вам успешно загестрировать в систему")
    return render_template('pre_login/register.html', 
                           message="")

def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = Users.query.filter_by(username=username).first()
        if user and password == user.password:
            return redirect(url_for('homepage_route')) 
        else:
            return render_template('pre_login/login.html', 
                                   message="Не правильно имя пользователя или пароль!")
    return render_template('pre_login/login.html')

def homepage():
    # 1. Диаграмма количества клиентов по гражданству
    nationalities = db.session.query(Customers.nationality, func.count().label("count")).group_by(Customers.nationality).all()
    bar1 = go.Figure([go.Bar(x=[n[0] for n in nationalities], y=[n[1] for n in nationalities])])
    bar1.update_layout(title="Количество клиентов по гражданству")

    # 2. Диаграмма количества бронирований по месяцам
    booking_months = db.session.query(
        func.date_format(Bookings.date_created, '%Y-%m'), 
        func.count()
    ).group_by(func.date_format(Bookings.date_created, '%Y-%m')).all()
    bar2 = go.Figure([go.Bar(x=[b[0] for b in booking_months], y=[b[1] for b in booking_months])])
    bar2.update_layout(title="Количество бронирований по месяцам")

    # 3. Круговая диаграмма методов оплаты
    payment_methods = db.session.query(Payment.payment_method, func.count()).group_by(Payment.payment_method).all()
    pie1 = go.Figure([go.Pie(labels=[p[0] for p in payment_methods], values=[p[1] for p in payment_methods])])
    pie1.update_layout(title="Распределение способов оплаты")

    # 4. Линейная диаграмма общей суммы оплат по месяцам
    payments_by_month = db.session.query(
        func.date_format(Payment.payment_date, '%Y-%m'),
        func.sum(Payment.amount)
    ).group_by(func.date_format(Payment.payment_date, '%Y-%m')).all()
    payments_by_month.sort(key=lambda x: x[0])
    line1 = go.Figure([go.Scatter(x=[p[0] for p in payments_by_month], y=[float(p[1]) for p in payments_by_month], mode='lines+markers')])
    line1.update_layout(title="Общая сумма оплат по месяцам")

    # 5. Диаграмма статусов бронирования
    booking_statuses = db.session.query(Bookings.booking_status, func.count()).group_by(Bookings.booking_status).all()
    bar3 = go.Figure([go.Bar(x=[b[0] for b in booking_statuses], y=[b[1] for b in booking_statuses])])
    bar3.update_layout(title="Количество бронирований по статусу")

    charts = [pio.to_html(fig, full_html=False) for fig in [bar1, bar2, pie1, line1, bar3]]
    return render_template("post_login/homepage.html", charts=charts)

def customer_content():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    filter_value = request.args.get('filter_value', '').strip().lower()

    query = Customers.query
    if filter_value:
        query = query.filter(Customers.customer_name.ilike(f"%{filter_value}%"))

    pagination = query.paginate(page=page, per_page=per_page)
    return render_template(
        'post_login/customer.html',
        customers=pagination.items,
        pagination=pagination,
        per_page=per_page,
        filter_value=filter_value
    )

def reset_password():
    message = ""
    if request.method == 'POST':
        username = request.form.get('username')
        personal_password = request.form.get('personal_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        user = Users.query.filter_by(username=username).first()
        personal_pass = Users.query.filter_by(personal_password=personal_password).first()
        if new_password != confirm_password:
            message = "Mật khẩu nhập lại không khớp!"
            return render_template('pre_login/reset_password.html', message=message)
        if not personal_pass:
            message = "mật khẩu riêng của nhân viên không hợp lệ!"
            return render_template('pre_login/reset_password.html', message=message)
        if not user:
            message = "Tên đăng nhập không tồn tại!"
            return render_template('pre_login/reset_password.html', message=message)
        
        user.password = new_password
        db.session.commit()
        return redirect(url_for('login_route'))  
    return render_template('pre_login/reset_password.html')

def bookings():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)
    filter_column = request.args.get("filter_column", "")
    filter_value = request.args.get("filter_value", "").strip().lower()

    query = Bookings.query

    if filter_column and filter_value:
        if filter_column == "booking_status":
            query = query.filter(Bookings.booking_status.ilike(f"%{filter_value}%"))
        elif filter_column == "checkin_date":
            query = query.filter(db.cast(Bookings.checkin_date, db.String).ilike(f"%{filter_value}%"))
        elif filter_column == "checkout_date":
            query = query.filter(db.cast(Bookings.checkout_date, db.String).ilike(f"%{filter_value}%"))
        elif filter_column == "date_created":
            query = query.filter(db.cast(Bookings.date_created, db.String).ilike(f"%{filter_value}%"))
        elif filter_column == "customer_id":
            query = query.filter(Bookings.customer_id.like(f"%{filter_value}%"))
        elif filter_column == "service_id":
            query = query.filter(Bookings.service_id.like(f"%{filter_value}%"))

    pagination = query.order_by(Bookings.booking_id.desc()).paginate(page=page, per_page=per_page)
    print("Số bản ghi truy vấn được:", pagination.total)
    for b in pagination.items[:5]:
        print(f"[DEBUG] Booking: ID={b.booking_id}, Customer={b.customer_id}, Status={b.booking_status}")
    return render_template(
        "post_login/bookings.html",
        bookings=pagination.items,
        pagination=pagination,
        per_page=per_page,
        filter_column=filter_column,
        filter_value=filter_value
    )

def save_bookings():
    new_booking = Bookings(
        customer_id=request.form['customer_id'],
        service_id=request.form['service_id'],
        checkin_date=request.form['checkin_date'],
        checkout_date=request.form['checkout_date'],
        booking_status=request.form['booking_status']
    )
    db.session.add(new_booking)
    db.session.commit()
    return redirect(url_for('bookings_route'))

def edit_bookings(booking_id):
    booking = Bookings.query.get_or_404(booking_id)
    booking.customer_id = request.form['customer_id']
    booking.service_id = request.form['service_id']
    booking.checkin_date = request.form['checkin_date']
    booking.checkout_date = request.form['checkout_date']
    booking.booking_status = request.form['booking_status']
    db.session.commit()
    return redirect(url_for('bookings_route'))

def delete_booking(booking_id):
    booking = Bookings.query.get(booking_id)
    db.session.delete(booking)
    db.session.commit()
    return redirect(url_for("bookings_route"))

def save_customer():
    new_customer = Customers(
        customer_name=request.form['customer_name'],
        dob=request.form['dob'],
        nationality=request.form['nationality'],
        email=request.form['email'],
        passport_number=request.form['passport_number'],
        personal_phone=request.form['personal_phone']
    )
    db.session.add(new_customer)
    db.session.commit()
    return redirect(url_for('customer_route'))

def edit_customer(customer_id):
    customer = Customers.query.get_or_404(customer_id)
    customer.customer_name = request.form['customer_name']
    customer.dob = request.form['dob']
    customer.nationality = request.form['nationality']
    customer.email = request.form['email']
    customer.passport_number = request.form['passport_number']
    customer.personal_phone = request.form['personal_phone']
    db.session.commit()
    return redirect(url_for('customer_route'))

def delete_customer(customer_id):
    customer = Customers.query.get_or_404(customer_id)
    db.session.delete(customer)
    db.session.commit()
    return redirect(url_for('customer_route'))

def payments():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)
    filter_value = request.args.get("filter_value", "").strip()

    query = Payment.query
    if filter_value:
        query = query.filter(Payment.booking_id.like(f"%{filter_value}%"))

    pagination = query.order_by(Payment.payment_id.desc()).paginate(page=page, per_page=per_page)
    return render_template("post_login/payment.html", payments=pagination.items, pagination=pagination, filter_value=filter_value, per_page=per_page)

def save_payments():
    payment_id = request.form.get("payment_id")
    booking_id = request.form.get("booking_id")
    amount = request.form.get("amount")
    method = request.form.get("payment_method")
    date = request.form.get("payment_date")

    if payment_id:
        payment = Payment.query.get(payment_id)
        if payment:
            payment.booking_id = booking_id
            payment.amount = amount
            payment.payment_method = method
            payment.payment_date = date
    else:
        payment = Payment(booking_id=booking_id, amount=amount, payment_method=method, payment_date=date)
        db.session.add(payment)

    db.session.commit()
    return redirect(url_for("payments_route"))

def delete_payments(payment_id):
    payment = Payment.query.get(payment_id)
    if payment:
        db.session.delete(payment)
        db.session.commit()
    return redirect(url_for("payments_route"))
