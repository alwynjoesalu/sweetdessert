from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.secret_key = 'sweet_secret_key_123'

# --- 1. Database Setup (Render PostgreSQL) ---
# PASTE YOUR RENDER INTERNAL DATABASE URL HERE:
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://your_render_username:your_render_password@your_render_hostname/your_db_name'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- 2. Database Models ---
class AdminUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    img = db.Column(db.String(50), nullable=False)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    customer_name = db.Column(db.String(80), nullable=False)
    status = db.Column(db.String(20), default='Pending')

# --- 3. Public Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/menu')
def menu():
    dynamic_menu = Product.query.all()
    return render_template('menu.html', menu=dynamic_menu)

# --- 4. Customer System ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = request.form.get('customer_name').strip()
        if name:
            session['customer_name'] = name
            session['is_admin'] = False
            return redirect(url_for('menu'))
        else:
            flash("Please enter your name to continue.")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/buy/<name>/<int:price>')
def buy(name, price):
    if 'customer_name' not in session or session.get('is_admin'):
        flash("Please tell us your name before ordering!")
        return redirect(url_for('login'))
    
    new_order = Order(
        product_name=name, 
        price=price, 
        customer_name=session['customer_name']
    )
    db.session.add(new_order)
    db.session.commit()
    return redirect(url_for('mybookings'))

@app.route('/mybookings')
def mybookings():
    if 'customer_name' not in session or session.get('is_admin'):
        return redirect(url_for('login'))
    
    current_user = session['customer_name']
    user_orders = Order.query.filter_by(customer_name=current_user).order_by(Order.id.desc()).all()
    
    total_bookings = len(user_orders)
    confirmed_bookings = sum(1 for order in user_orders if order.status == 'Confirmed')
    
    return render_template('mybookings.html', 
                           orders=user_orders, 
                           customer_name=current_user,
                           total=total_bookings,
                           confirmed=confirmed_bookings)

@app.route('/cancel_booking/<int:order_id>')
def cancel_booking(order_id):
    if 'customer_name' not in session:
        return redirect(url_for('login'))
        
    order = Order.query.get(order_id)
    if order and order.customer_name == session['customer_name'] and order.status == 'Pending':
        order.status = 'Cancelled'
        db.session.commit()
    return redirect(url_for('mybookings'))

# --- 5. Admin System ---
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        admin = AdminUser.query.filter_by(username=request.form['username']).first()
        if admin and admin.password == request.form['password']:
            session['is_admin'] = True
            session['admin_name'] = admin.username
            return redirect(url_for('admin'))
        else:
            flash("Invalid Admin credentials!")
    return render_template('admin_login.html')

@app.route('/admin')
def admin():
    if not session.get('is_admin'):
        return redirect(url_for('admin_login'))
    
    all_orders = Order.query.order_by(Order.id.desc()).all()
    return render_template('admin.html', orders=all_orders)

@app.route('/confirm_order/<int:order_id>')
def confirm_order(order_id):
    if not session.get('is_admin'):
        return redirect(url_for('admin_login'))
    
    order = Order.query.get(order_id)
    if order and order.status == 'Pending':
        order.status = 'Confirmed'
        db.session.commit()
    return redirect(url_for('admin'))

# --- 6. Auto-Initialization ---
if __name__ == '__main__':
    with app.app_context():
        # Creates tables in the Cloud Database if they don't exist
        db.create_all()
        
        # Auto-create Admin Account
        if not AdminUser.query.filter_by(username='admin').first():
            db.session.add(AdminUser(username='admin', password='123'))
            db.session.commit()
            print("Cloud Admin account created (admin / 123)")
            
        # Auto-populate Menu Items if the table is empty
        if Product.query.count() == 0:
            default_items = [
                Product(name="Lou'a Nutella", price=349, img="nutella.png"),
                Product(name="Lou'a Pistachio Lotus", price=349, img="pistachio.png"),
                Product(name="Lou'a Kinder", price=349, img="kinder.png"),
                Product(name="Cheese Bomb", price=290, img="cheese_bomb.png"),
                Product(name="Kabsa Dessert", price=380, img="kabsa.png")
            ]
            db.session.add_all(default_items)
            db.session.commit()
            print("Menu items added to Cloud Database!")

    app.run(debug=True)
