"""All SQLite connections, tables and SQL are kept here."""
import sqlite3
from pathlib import Path


class Database:
    def __init__(self, filename):
        self.filename = filename

    def connect(self):
        connection = sqlite3.connect(self.filename)
        connection.row_factory = sqlite3.Row
        connection.execute('PRAGMA foreign_keys = ON')
        return connection

    def query(self, sql, values=(), one=False):
        connection = self.connect()
        try:
            cursor = connection.execute(sql, values)
            if one:
                return cursor.fetchone()
            return cursor.fetchall()
        finally:
            connection.close()

    def execute(self, sql, values=()):
        connection = self.connect()
        try:
            cursor = connection.execute(sql, values)
            connection.commit()
            return cursor.lastrowid
        finally:
            connection.close()

    def create_tables(self):
        connection = self.connect()
        try:
            schema_file = Path(__file__).with_name('schema.sql')
            with open(schema_file, encoding='utf-8') as file:
                connection.executescript(file.read())
            connection.commit()
        finally:
            connection.close()


class User:
    def __init__(self, database):
        self.database = database

    def find(self, username):
        return self.database.query('SELECT * FROM users WHERE username = ?', (username,), one=True)

    def get(self, user_id):
        return self.database.query('SELECT * FROM users WHERE id = ?', (user_id,), one=True)

    def create(self, username, password):
        self.database.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))


    def save_preferences(self, user_id, values):
        self.database.execute(
            'UPDATE users SET vegan=?, vegetarian=?, gluten_free=?, lactose_free=? WHERE id=?',
            (values[0], values[1], values[2], values[3], user_id))


class Recipe:
    def __init__(self, database):
        self.database = database

    def get(self, recipe_id, user_id):
        return self.database.query('SELECT * FROM recipes WHERE id = ? AND user_id = ?',
                                (recipe_id, user_id), one=True)

    def search(self, user_id, filters):
        sql = 'SELECT * FROM recipes WHERE user_id = ?'
        values = [user_id]
        for field in ('name', 'ingredients'):
            if filters.get(field):
                sql += f' AND {field} LIKE ?'
                values.append('%' + filters[field] + '%')
        for field, operator in [('rating', '>='), ('cooking_time', '<=')]:
            value = filters.get(field, '')
            if value.isdigit():
                sql += f' AND {field} {operator} ?'
                values.append(int(value))
        if filters.get('collection', '').isdigit():
            sql += ' AND id IN (SELECT recipe_id FROM collection_recipes WHERE collection_id = ?)'
            values.append(int(filters['collection']))
        orders = {'name': 'name COLLATE NOCASE ASC', 'name_desc': 'name COLLATE NOCASE DESC',
                  'rating': 'rating DESC, name COLLATE NOCASE', 'time': 'cooking_time ASC'}
        sql += ' ORDER BY ' + orders.get(filters.get('sort'), orders['name'])
        return self.database.query(sql, values)


    def collection_ids(self, recipe_id):
        rows = self.database.query(
            'SELECT collection_id FROM collection_recipes WHERE recipe_id=?', (recipe_id,))
        return [row['collection_id'] for row in rows]

    def save(self, recipe_id, user_id, values, collection_ids):
        name, rating, cooking_time, ingredients, instructions, picture = values
        connection = self.database.connect()
        try:
            if recipe_id is None:
                cursor = connection.execute(
                    'INSERT INTO recipes (name,rating,cooking_time,ingredients,instructions,picture,user_id) VALUES (?,?,?,?,?,?,?)',
                    (name, rating, cooking_time, ingredients, instructions, picture, user_id))
                recipe_id = cursor.lastrowid
            else:
                connection.execute(
                    'UPDATE recipes SET name=?,rating=?,cooking_time=?,ingredients=?,instructions=?,picture=? WHERE id=? AND user_id=?',
                    (name, rating, cooking_time, ingredients, instructions, picture, recipe_id, user_id))
            connection.execute('DELETE FROM collection_recipes WHERE recipe_id=?', (recipe_id,))
            for collection_id in set(collection_ids):
                connection.execute('INSERT INTO collection_recipes VALUES (?,?)', (collection_id, recipe_id))
            connection.commit()
            return recipe_id
        finally:
            connection.close()

    def delete(self, recipe_id):
        self.database.execute('DELETE FROM recipes WHERE id=?', (recipe_id,))

    def rate(self, recipe_id, rating):
        self.database.execute('UPDATE recipes SET rating=? WHERE id=?', (rating, recipe_id))


class Collection:
    def __init__(self, database):
        self.database = database

    def all(self, user_id):
        return self.database.query('''SELECT c.*, COUNT(cr.recipe_id) AS recipe_count
            FROM collections c LEFT JOIN collection_recipes cr ON cr.collection_id = c.id
            WHERE c.user_id = ? GROUP BY c.id ORDER BY c.name COLLATE NOCASE''', (user_id,))

    def get(self, collection_id, user_id):
        return self.database.query('SELECT * FROM collections WHERE id = ? AND user_id = ?',
                                (collection_id, user_id), one=True)


    def for_recipe(self, recipe_id, user_id):
        return self.database.query(
            'SELECT c.* FROM collections c JOIN collection_recipes cr ON c.id=cr.collection_id WHERE cr.recipe_id=? AND c.user_id=?',
            (recipe_id, user_id))

    def recipe_ids(self, collection_id):
        rows = self.database.query(
            'SELECT recipe_id FROM collection_recipes WHERE collection_id=?', (collection_id,))
        return [row['recipe_id'] for row in rows]

    def save(self, collection_id, user_id, name, picture, recipe_ids):
        connection = self.database.connect()
        try:
            if collection_id is None:
                cursor = connection.execute(
                    'INSERT INTO collections (name,picture,user_id) VALUES (?,?,?)', (name, picture, user_id))
                collection_id = cursor.lastrowid
            else:
                connection.execute('UPDATE collections SET name=?,picture=? WHERE id=?',
                                   (name, picture, collection_id))
            connection.execute('DELETE FROM collection_recipes WHERE collection_id=?', (collection_id,))
            for recipe_id in set(recipe_ids):
                connection.execute('INSERT INTO collection_recipes VALUES (?,?)', (collection_id, recipe_id))
            connection.commit()
            return collection_id
        finally:
            connection.close()

    def delete(self, collection_id):
        self.database.execute('DELETE FROM collections WHERE id=?', (collection_id,))


class Substitution:
    def __init__(self, database):
        self.database = database

    def all(self):
        # Longer names are matched first, for example wheat flour before flour.
        return self.database.query(
            'SELECT * FROM substitutions ORDER BY LENGTH(ingredient) DESC, id')
