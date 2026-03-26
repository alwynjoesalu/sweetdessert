from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = 'sweet_secret_key_123'

# --- 1. Database Setup (Render PostgreSQL) ---
# PASTE YOUR RENDER INTERNAL DATABASE URL HERE:
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

# NEW: The Secure Customer Model
class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    # We now store the customer's unique ID, not just their name
    customer_id = db.Column(db.Integer, nullable=False) 
    customer_name = db.Column(db.String(80), nullable=False) # Kept for easy admin viewing
    status = db.Column(db.String(20), default='Pending')

# --- 3. Auto-Initialization ---
with app.app_context():
    # If you get an error about "column customer_id doesn't exist", uncomment the line below for ONE run to reset the database, then comment it out again.
    # db.drop_all() 
    db.create_all()
    
    if not AdminUser.query.filter_by(username='admin').first():
        db.session.add(AdminUser(username='admin', password='123'))
        db.session.commit()
        
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

# --- 5. NEW Secure Customer System ---
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
            session['
