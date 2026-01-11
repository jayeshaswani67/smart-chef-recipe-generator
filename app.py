from flask import Flask, render_template, redirect, url_for, flash, request, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import sqlite3
import os
from datetime import datetime
import re
import random

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this for production
app.config['DATABASE'] = 'smartchef.db'

# Recipe data
RECIPE_TYPES = ['Breakfast', 'Lunch', 'Dinner', 'Dessert', 'Snack']
CUISINES = ['Italian', 'Mexican', 'Indian', 'Chinese', 'American', 'Mediterranean']
INGREDIENTS = {
    'Vegetables': ['Tomatoes', 'Onions', 'Garlic', 'Bell Peppers', 'Carrots', 'Broccoli'],
    'Proteins': ['Chicken', 'Beef', 'Fish', 'Tofu', 'Eggs', 'Beans'],
    'Grains': ['Rice', 'Pasta', 'Quinoa', 'Bread', 'Couscous'],
    'Dairy': ['Milk', 'Cheese', 'Yogurt', 'Butter'],
    'Spices': ['Salt', 'Pepper', 'Cumin', 'Paprika', 'Turmeric', 'Cinnamon']
}

# Database setup
def get_db():
    db = sqlite3.connect(app.config['DATABASE'])
    db.row_factory = sqlite3.Row
    return db

def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        ''')
        
        # Recipes table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS recipes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                ingredients TEXT NOT NULL,
                instructions TEXT NOT NULL,
                recipe_type TEXT NOT NULL,
                cuisine TEXT NOT NULL,
                user_id INTEGER,
                created_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')
        
        # Saved recipes table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS saved_recipes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                recipe_id INTEGER NOT NULL,
                saved_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id),
                FOREIGN KEY(recipe_id) REFERENCES recipes(id)
            )
        ''')
        db.commit()

# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page', 'danger')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# Recipe generation
def generate_recipe(ingredients=None, recipe_type=None, cuisine=None):
    # Select random type and cuisine if not specified
    recipe_type = recipe_type or random.choice(RECIPE_TYPES)
    cuisine = cuisine or random.choice(CUISINES)
    
    # Generate recipe title
    title = f"{cuisine} {recipe_type} with {random.choice(ingredients or ['Fresh Ingredients'])}"
    
    # Generate instructions
    instructions = [
        f"Prepare all your ingredients: {', '.join(ingredients or ['available ingredients'])}.",
        f"Heat a pan over medium heat and add some oil.",
        f"Cook according to {cuisine} style, seasoning with {random.choice(INGREDIENTS['Spices'])}.",
        "Serve hot and enjoy!"
    ]
    
    return {
        'title': title,
        'type': recipe_type,
        'cuisine': cuisine,
        'ingredients': ingredients or ['Sample ingredient 1', 'Sample ingredient 2'],
        'instructions': instructions,
        'image': f"/static/images/recipe-{random.randint(1, 6)}.jpg"
    }

# Routes
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('home'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        
        if not email or not password:
            flash('Please fill in all fields', 'danger')
            return redirect(url_for('login'))
        
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid email or password', 'danger')
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validation
        errors = False
        
        if not username:
            flash('Username is required', 'danger')
            errors = True
        if not email:
            flash('Email is required', 'danger')
            errors = True
        elif not re.match(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$', email):
            flash('Invalid email address', 'danger')
            errors = True
        if not password:
            flash('Password is required', 'danger')
            errors = True
        elif len(password) < 8:
            flash('Password must be at least 8 characters', 'danger')
            errors = True
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            errors = True
        
        if not errors:
            db = get_db()
            cursor = db.cursor()
            
            # Check if username or email exists
            cursor.execute('SELECT id FROM users WHERE username = ? OR email = ?', (username, email))
            if cursor.fetchone():
                flash('Username or email already registered', 'danger')
            else:
                hashed_pw = generate_password_hash(password)
                created_at = datetime.now().isoformat()
                
                try:
                    cursor.execute('''
                        INSERT INTO users (username, email, password, created_at)
                        VALUES (?, ?, ?, ?)
                    ''', (username, email, hashed_pw, created_at))
                    db.commit()
                    
                    # Get the new user's ID
                    cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
                    user = cursor.fetchone()
                    
                    session['user_id'] = user['id']
                    session['username'] = username
                    flash('Account created successfully!', 'success')
                    return redirect(url_for('home'))
                except sqlite3.Error as e:
                    db.rollback()
                    flash('An error occurred. Please try again.', 'danger')
    
    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash('You have been logged out', 'success')
    return redirect(url_for('login'))

@app.route('/home')
@login_required
def home():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        SELECT * FROM recipes 
        WHERE user_id = ? 
        ORDER BY created_at DESC
        LIMIT 3
    ''', (session['user_id'],))
    recipes = cursor.fetchall()
    return render_template('home.html', username=session.get('username'), recipes=recipes)

@app.route('/generate-recipe', methods=['GET', 'POST'])
@login_required
def generate_recipe_route():
    if request.method == 'POST':
        ingredients = request.form.getlist('ingredients')
        recipe_type = request.form.get('recipe_type')
        cuisine = request.form.get('cuisine')
        
        recipe = generate_recipe(ingredients, recipe_type, cuisine)
        
        # Save to database
        db = get_db()
        cursor = db.cursor()
        created_at = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO recipes (title, ingredients, instructions, recipe_type, cuisine, user_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            recipe['title'],
            ', '.join(recipe['ingredients']),
            '\n'.join(recipe['instructions']),
            recipe['type'],
            recipe['cuisine'],
            session['user_id'],
            created_at
        ))
        db.commit()
        
        return render_template('recipe_result.html', recipe=recipe)
    
    return render_template('generate_recipe.html', 
                         recipe_types=RECIPE_TYPES, 
                         cuisines=CUISINES,
                         ingredients=INGREDIENTS)

@app.route('/api/find-recipes', methods=['POST'])
@login_required
def api_find_recipes():
    data = request.get_json()
    ingredients = data.get('ingredients', [])
    recipe_type = data.get('recipeType')
    cuisine = data.get('cuisine')
    
    # In a real app, you would query your database here
    # For demo purposes, we'll generate some mock recipes
    num_recipes = random.randint(2, 5)
    recipes = [generate_recipe(ingredients, recipe_type, cuisine) for _ in range(num_recipes)]
    
    return jsonify({
        'success': True,
        'recipes': recipes
    })

@app.route('/api/bookmark-recipe', methods=['POST'])
@login_required
def api_bookmark_recipe():
    data = request.get_json()
    recipe_id = data.get('recipe_id')
    action = data.get('action')
    
    if not recipe_id or action not in ['add', 'remove']:
        return jsonify({'success': False, 'message': 'Invalid request'}), 400
    
    db = get_db()
    cursor = db.cursor()
    
    try:
        if action == 'add':
            cursor.execute('''
                INSERT INTO saved_recipes (user_id, recipe_id, saved_at)
                VALUES (?, ?, ?)
            ''', (session['user_id'], recipe_id, datetime.now().isoformat()))
        else:
            cursor.execute('''
                DELETE FROM saved_recipes 
                WHERE user_id = ? AND recipe_id = ?
            ''', (session['user_id'], recipe_id))
        
        db.commit()
        return jsonify({'success': True})
    except sqlite3.Error as e:
        db.rollback()
        return jsonify({'success': False, 'message': 'Database error'}), 500

@app.route('/recipes')
@login_required
def recipes():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        SELECT * FROM recipes 
        WHERE user_id = ? 
        ORDER BY created_at DESC
    ''', (session['user_id'],))
    recipes = cursor.fetchall()
    return render_template('recipes.html', recipes=recipes)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        
        if not name or not email or not message:
            flash('Please fill in all fields', 'danger')
        elif not re.match(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$', email):
            flash('Invalid email address', 'danger')
        else:
            # In a real app, you would save this to a database or send an email
            flash('Your message has been sent! We will contact you soon.', 'success')
            return redirect(url_for('contact'))
    
    return render_template('contact.html')

@app.route('/api/recipes/popular')
def popular_recipes():
    # In a real app, you would query your database for popular recipes
    # For demo purposes, we'll return mock data
    mock_recipes = [
        {
            'id': 1,
            'title': 'Vegetable Stir Fry',
            'image_url': '/static/images/recipe-1.jpg',
            'rating': 4,
            'review_count': 128,
            'cook_time': 20,
            'difficulty': 'Easy'
        },
        {
            'id': 2,
            'title': 'Creamy Pasta',
            'image_url': '/static/images/recipe-2.jpg',
            'rating': 5,
            'review_count': 95,
            'cook_time': 25,
            'difficulty': 'Medium'
        },
        {
            'id': 3,
            'title': 'Chicken Curry',
            'image_url': '/static/images/recipe-3.jpg',
            'rating': 4,
            'review_count': 76,
            'cook_time': 35,
            'difficulty': 'Medium'
        }
    ]
    return jsonify(mock_recipes)

if __name__ == '__main__':
    if not os.path.exists(app.config['DATABASE']):
        init_db()
    app.run(debug=True)