"""Run this file to start the recipe book."""
from pathlib import Path
import os
import secrets
import sqlite3
from uuid import uuid4

from flask import Flask, abort, flash, redirect, render_template, request, session, url_for
from PIL import Image, UnidentifiedImageError
from werkzeug.security import check_password_hash, generate_password_hash
from database import Database, User, Recipe, Collection, Substitution
from substitutions import suggest

app = Flask(__name__)
Path(app.instance_path).mkdir(exist_ok=True)
secret_file = Path(app.instance_path) / 'secret_key'
if not secret_file.exists():
    secret_file.write_text(secrets.token_hex(32))
app.secret_key = os.environ.get('SECRET_KEY') or secret_file.read_text()
app.config['UPLOAD_FOLDER'] = str(Path(app.root_path) / 'static' / 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024
Path(app.config['UPLOAD_FOLDER']).mkdir(parents=True, exist_ok=True)

database = Database(str(Path(app.instance_path) / 'recipes.db'))
database.create_tables()
users = User(database)
recipes = Recipe(database)
collections_db = Collection(database)
substitutions_db = Substitution(database)

DIETS = {'vegan': 'Vegan', 'vegetarian': 'Vegetarian',
         'gluten_free': 'Gluten-free', 'lactose_free': 'Lactose-free'}


def show_page(filename, **values):
    # All pages need the menu, dietary labels and a form token.
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(24)
    user = users.get(session['user_id']) if 'user_id' in session else None
    return render_template(filename, user=user, diets=DIETS, **values)


def check_form():
    # A submitted form must have the same token as the user's session.
    if request.method == 'POST':
        saved_token = session.get('csrf_token', '')
        form_token = request.form.get('csrf_token', '')
        if not saved_token or not secrets.compare_digest(saved_token, form_token):
            abort(400, 'The form expired. Refresh the page and try again.')


def owned_recipe(recipe_id):
    recipe = recipes.get(recipe_id, session['user_id'])
    if recipe is None:
        abort(404)
    return recipe

def owned_collection(collection_id):
    collection = collections_db.get(collection_id, session['user_id'])
    if collection is None:
        abort(404)
    return collection

def save_picture(old_picture=None):
    upload = request.files.get('picture')
    if not upload or not upload.filename:
        return None if request.form.get('remove_picture') else old_picture
    try:
        with Image.open(upload.stream) as picture:
            if picture.format not in ('JPEG', 'PNG', 'WEBP'):
                raise ValueError('Use a JPG, PNG or WebP image.')
            picture.thumbnail((1400, 1400))
            filename = uuid4().hex + '.jpg'
            picture.convert('RGB').save(Path(app.config['UPLOAD_FOLDER']) / filename, 'JPEG', quality=85)
            return filename
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
        raise ValueError('Please choose a valid JPG, PNG or WebP image.')

def clean_old_picture(old, new):
    if old and old != new:
        (Path(app.config['UPLOAD_FOLDER']) / old).unlink(missing_ok=True)

@app.route('/register', methods=['GET', 'POST'])
def register():
    check_form()
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        if not 3 <= len(username) <= 40 or len(password) < 8:
            flash('Use a username of 3–40 characters and a password of at least 8 characters.', 'error')
        else:
            try:
                users.create(username, generate_password_hash(password))
                session.clear()
                session['user_id'] = users.find(username)['id']
                return redirect(url_for('index'))
            except sqlite3.IntegrityError:
                flash('That username is already taken.', 'error')
    return show_page('auth.html', registering=True)

@app.route('/login', methods=['GET', 'POST'])
def login():
    check_form()
    if request.method == 'POST':
        user = users.find(request.form.get('username', '').strip())
        if user and check_password_hash(user['password'], request.form.get('password', '')):
            session.clear()
            session['user_id'] = user['id']
            return redirect(url_for('index'))
        flash('Incorrect username or password.', 'error')
    return show_page('auth.html', registering=False)

@app.route('/logout', methods=['POST'])
def logout():
    check_form()
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = users.get(session['user_id'])
    return show_page('index.html', recipes=recipes.search(user['id'], request.args),
                           collections=collections_db.all(user['id']))

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    check_form()
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = users.get(session['user_id'])
    if request.method == 'POST':
        values = [int(key in request.form) for key in DIETS]
        users.save_preferences(user['id'], values)
        flash('Your dietary preferences were saved.', 'success')
        return redirect(url_for('profile'))
    return show_page('profile.html')

@app.route('/recipes/<int:recipe_id>')
def recipe_detail(recipe_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = users.get(session['user_id'])
    recipe = owned_recipe(recipe_id)
    collections = collections_db.for_recipe(recipe_id, user['id'])
    return show_page('recipe.html', recipe=recipe, collections=collections,
                           suggestions=suggest(recipe['ingredients'], user, substitutions_db.all()))

@app.route('/recipes/new', methods=['GET', 'POST'])
@app.route('/recipes/<int:recipe_id>/edit', methods=['GET', 'POST'])
def recipe_form(recipe_id=None):
    check_form()
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = users.get(session['user_id'])
    recipe = owned_recipe(recipe_id) if recipe_id else None
    selected = recipes.collection_ids(recipe_id)
    if request.method == 'POST':
        selected = request.form.getlist('collections', type=int)
        allowed = {c['id'] for c in collections_db.all(user['id'])}
        try:
            name = request.form.get('name', '').strip()
            ingredients = request.form.get('ingredients', '').strip()
            instructions = request.form.get('instructions', '').strip()
            rating = int(request.form.get('rating', '0'))
            cooking_time = int(request.form.get('cooking_time', '0'))
            if not name or len(name) > 120 or not ingredients or not instructions:
                raise ValueError('Add a name (up to 120 characters), ingredients and instructions.')
            if not 0 <= rating <= 5 or not 1 <= cooking_time <= 10080:
                raise ValueError('Rating must be 0–5 and cooking time 1–10080 minutes.')
            if not set(selected) <= allowed:
                abort(400)
            picture = save_picture(recipe['picture'] if recipe else None)
            values = (name, rating, cooking_time, ingredients, instructions, picture)
            recipe_id = recipes.save(recipe_id, user['id'], values, selected)
            clean_old_picture(recipe['picture'] if recipe else None, picture)
            flash('Recipe saved.', 'success')
            return redirect(url_for('recipe_detail', recipe_id=recipe_id))
        except ValueError as error:
            flash(str(error) or 'Enter valid numbers for rating and cooking time.', 'error')
    return show_page('recipe_form.html', recipe=recipe, selected=selected,
                           collections=collections_db.all(user['id']))

@app.route('/recipes/<int:recipe_id>/delete', methods=['POST'])
def delete_recipe(recipe_id):
    check_form()
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = users.get(session['user_id'])
    recipe = owned_recipe(recipe_id)
    recipes.delete(recipe_id)
    clean_old_picture(recipe['picture'], None)
    flash('Recipe deleted.', 'success')
    return redirect(url_for('index'))

@app.route('/recipes/<int:recipe_id>/rate', methods=['POST'])
def rate_recipe(recipe_id):
    check_form()
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = users.get(session['user_id'])
    owned_recipe(recipe_id)
    rating = request.form.get('rating', type=int)
    if rating is None or not 0 <= rating <= 5:
        abort(400)
    recipes.rate(recipe_id, rating)
    return redirect(url_for('recipe_detail', recipe_id=recipe_id))

@app.route('/collections')
def collections():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = users.get(session['user_id'])
    return show_page('collections.html', collections=collections_db.all(user['id']))

@app.route('/collections/<int:collection_id>')
def collection_detail(collection_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = users.get(session['user_id'])
    collection = owned_collection(collection_id)
    filters = request.args.to_dict()
    filters['collection'] = str(collection_id)
    return show_page('index.html', collection=collection,
                           recipes=recipes.search(user['id'], filters),
                           collections=collections_db.all(user['id']))

@app.route('/collections/new', methods=['GET', 'POST'])
@app.route('/collections/<int:collection_id>/edit', methods=['GET', 'POST'])
def collection_form(collection_id=None):
    check_form()
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = users.get(session['user_id'])
    collection = owned_collection(collection_id) if collection_id else None
    selected = collections_db.recipe_ids(collection_id)
    if request.method == 'POST':
        selected = request.form.getlist('recipes', type=int)
        try:
            name = request.form.get('name', '').strip()
            if not name or len(name) > 120:
                raise ValueError('Give your collection a name of 1–120 characters.')
            allowed = {r['id'] for r in recipes.search(user['id'], {})}
            if not set(selected) <= allowed:
                abort(400)
            picture = save_picture(collection['picture'] if collection else None)
            collection_id = collections_db.save(collection_id, user['id'], name, picture, selected)
            clean_old_picture(collection['picture'] if collection else None, picture)
            flash('Collection saved.', 'success')
            return redirect(url_for('collection_detail', collection_id=collection_id))
        except ValueError as error:
            flash(str(error), 'error')
    return show_page('collection_form.html', collection=collection, selected=selected,
                           recipes=recipes.search(user['id'], {}))

@app.route('/collections/<int:collection_id>/delete', methods=['POST'])
def delete_collection(collection_id):
    check_form()
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = users.get(session['user_id'])
    collection = owned_collection(collection_id)
    collections_db.delete(collection_id)
    clean_old_picture(collection['picture'], None)
    flash('Collection deleted. Its recipes are still in your recipe book.', 'success')
    return redirect(url_for('collections'))


if __name__ == '__main__':
    app.run(debug=True)
