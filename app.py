from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = 'sweet_secret_key_123'

# --- 1. Database Setup (Render PostgreSQL) ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://sweet_dessert_db_user:T2ET8fNCErfgWD9hFtkcVTPPBczIllvW@dpg-d72oadeuk2gs73euhs8g-a/sweet_dessert_db'
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

# The Secure Customer Model
class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    customer_id = db.Column(db.Integer, nullable=False) 
    customer_name = db.Column(db.String(80), nullable=False)
    status = db.Column(db.String(20), default='Pending')

# --- 3. Auto-Initialization ---
with app.app_context():
    # db.drop_all() # Uncomment this line temporarily if you need to wipe old data
    db.create_all()
    
    if not AdminUser.query.filter_by(username='admin').first():
        db.session.add(AdminUser(username='admin', password='123'))
        db.session.commit()
        print("Admin account verified")
        
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

# --- 4. Public Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/menu')
def menu():
    dynamic_menu = Product.query.all()
    return render_template('menu.html', menu=dynamic_menu)

# --- 5. Secure Customer System ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name').strip()
        email = request.form.get('email').strip().lower()
        password = request.form.get('password')

        # Check if email already exists
        existing_user = Customer.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already registered. Please log in.")
            return redirect(url_for('login'))

        # Securely hash the password
        hashed_pw = generate_password_hash(password)
        new_customer = Customer(name=name, email=email, password_hash=hashed_pw)
        
        db.session.add(new_customer)
        db.session.commit()
        
        flash("Registration successful! Please log in.")
        return redirect(url_for('login'))
        
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email').strip().lower()
        password = request.form.get('password')
        
        customer = Customer.query.filter_by(email=email).first()
        
        # Verify user exists and password matches the hash
        if customer and check_password_hash(customer.password_hash, password):
            session['customer_id'] = customer.id
            session['customer_name'] = customer.name
            session['is_admin'] = False
            return redirect(url_for('menu'))
        else:
            flash("Invalid email or password.")
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# --- 6. Buying & Bookings ---
@app.route('/buy/<name>/<int:price>')
def buy(name, price):
    if 'customer_id' not in session or session.get('is_admin'):
        flash("Please log in to your account before ordering!")
        return redirect(url_for('login'))
    
    new_order = Order(
        product_name=name, 
        price=price, 
        customer_id=session['customer_id'],
        customer_name=session['customer_name']
    )
    db.session.add(new_order)
    db.session.commit()
    return redirect(url_for('mybookings'))

@app.route('/mybookings')
def mybookings():
    if 'customer_id' not in session or session.get('is_admin'):
        return redirect(url_for('login'))
    
    # Orders are now filtered by the secure customer ID
    user_orders = Order.query.filter_by(customer_id=session['customer_id']).order_by(Order.id.desc()).all()
    
    total_bookings = len(user_orders)
    confirmed_bookings = sum(1 for order in user_orders if order.status == 'Confirmed')
    
    return render_template('mybookings.html', 
                           orders=user_orders, 
                           customer_name=session['customer_name'],
                           total=total_bookings,
                           confirmed=confirmed_bookings)

@app.route('/cancel_booking/<int:order_id>')
def cancel_booking(order_id):
    if 'customer_id' not in session:
        return redirect(url_for('login'))
        
    order = Order.query.get(order_id)
    if order and order.customer_id == session['customer_id'] and order.status == 'Pending':
        order.status = 'Cancelled'
        db.session.commit()
    return redirect(url_for('mybookings'))

# --- 7. Admin System ---
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

if __name__ == '__main__':
    app.run(debug=True)
