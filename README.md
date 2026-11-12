# Recipe Management System

A small IB project using Python, Flask, SQLite, HTML and CSS. Flask renders the pages, so there is no API or frontend framework. `app.py` uses ordinary route functions and explicit login checks. Each database operation opens and closes its own connection in `database.py`, without Flask lifecycle hooks or custom decorators. The only JavaScript asks for confirmation before deletion.

## Run locally

Python 3.10 or newer is required.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 app.py
```

Open http://127.0.0.1:5000 and register an account. No database installation or configuration is needed. The app starts empty; add your own recipes and collections, or load the photo examples below.

On Windows, activate with `.venv\Scripts\activate` instead.

## Features

- Registration, login and logout with hashed passwords.
- Private recipes with a name, rating (0 = unrated, 1–5 stars), cooking time in minutes, ingredients, instructions and optional image.
- Create, view, edit and delete recipes and collections.
- A recipe can belong to several collections. Manage membership in either edit form. Deleting a collection keeps its recipes.
- Filter by name, ingredient, minimum rating, maximum cooking time and collection. Sort alphabetically in either direction, by highest rating or by shortest cooking time. Filters can be combined.
- Saved vegan, vegetarian, gluten-free and lactose-free preferences.
- Recipe pages show alternative ingredients based on those preferences. The original recipe is kept. These are simple word-based suggestions, not a complete dietary/allergy checker. They preserve written quantities, which may need adjusting; cooking instructions are not automatically rewritten.
- Optional JPG, PNG and WebP uploads, limited to a 5 MB request. Images are validated and saved as resized JPEGs.

## Code layout

| File | Purpose |
| --- | --- |
| `app.py` | Flask setup, routes, form validation, authentication and images |
| `database.py` | SQLite connections, queries and database classes |
| `schema.sql` | Table definitions and default ingredient substitutions |
| `substitutions.py` | Matches ingredients against substitutions loaded from SQLite |
| `templates/` | HTML pages using Flask's Jinja templates |
| `static/style.css` | Responsive styling |
| `static/app.js` | Delete confirmation (6 lines) |
| `tests/test_app.py` | Tests using an isolated temporary SQLite database |

The database is created from `schema.sql` when the app starts. It contains `users`, `recipes`, `substitutions`, `collections` and `collection_recipes`. The last table links collections and recipes. The `substitutions` table stores an ingredient, its replacement and the dietary preference it applies to. Default substitutions are inserted from the SQL file without duplicating existing rows or deleting saved data. Recipe pages read suggestions from this table. Foreign keys remove links automatically when a recipe or collection is deleted. SQL parameters keep submitted values separate from SQL statements. Routes check ownership before accessing or changing records. Forms include a session token to prevent cross-site form submissions.

## Data

The database is created at `instance/recipes.db`. A local session signing key is saved at `instance/secret_key`; an optional `SECRET_KEY` environment variable overrides it. Pictures live in `static/uploads/`. Uploaded pictures are served as static files and are not access-controlled; recipe and collection pages are account-protected. This is a local coursework app: run it on your own computer. The development server uses debug mode and is not configured for public hosting.

Back up `instance/` and `static/uploads/` together to preserve data. To reset the app, stop it and delete `instance/recipes.db` and the uploaded images. The database is recreated on the next start.

## Tests

With the virtual environment activated:

```bash
python -m unittest discover -s tests -v
```

Tests cover accounts, CSRF tokens, CRUD, collection membership, filtering, sorting, ratings, ownership, preferences, substitutions and image validation/removal.

## Photo example recipes

The nine supplied photos are saved in `examples/`, with recipe data in `examples/recipes.json`. The ingredients and methods are approximate examples inspired by the pictures. Times include chilling and resting; ratings start at 0 (unrated).

After registering an account, run:

```bash
python seed_examples.py your_username
```

This adds nine recipes in four collections: Cakes, Cookies, Bread, and Tarts and pastries. Running it again skips recipes with the same name without overwriting edits. The examples have already been added to the existing `test` account in this workspace.
