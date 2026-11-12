"""Add the photo examples to an existing account: python seed_examples.py username"""
import argparse
import json
from pathlib import Path
import shutil
from uuid import uuid4

from database import Database, User, Recipe, Collection


def add_examples(database, username, upload_folder):
    user = User(database).find(username)
    if user is None:
        raise ValueError('Account not found. Register this username in the app first.')

    recipes = Recipe(database)
    collections = Collection(database)
    folder = Path(__file__).parent / 'examples'
    with open(folder / 'recipes.json', encoding='utf-8') as file:
        examples = json.load(file)

    Path(upload_folder).mkdir(parents=True, exist_ok=True)
    existing_names = {recipe['name'] for recipe in recipes.search(user['id'], {})}
    collection_ids = {item['name']: item['id'] for item in collections.all(user['id'])}
    added = 0
    for example in examples:
        # Running this script again leaves existing recipes alone.
        if example['name'] in existing_names:
            continue
        picture = uuid4().hex + '.jpg'
        shutil.copyfile(folder / example['picture'], Path(upload_folder) / picture)
        group = example['collection']
        if group not in collection_ids:
            collection_ids[group] = collections.save(None, user['id'], group, None, [])
        values = (example['name'], example['rating'], example['cooking_time'],
                  example['ingredients'], example['instructions'], picture)
        recipes.save(None, user['id'], values, [collection_ids[group]])
        existing_names.add(example['name'])
        added += 1
    return added


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Add the nine photo example recipes.')
    parser.add_argument('username', help='An existing account to receive the examples')
    arguments = parser.parse_args()
    root = Path(__file__).parent
    database = Database(str(root / 'instance' / 'recipes.db'))
    if not Path(database.filename).exists():
        parser.error('Start the app and register an account first.')
    database.create_tables()
    try:
        count = add_examples(database, arguments.username, root / 'static' / 'uploads')
    except ValueError as error:
        parser.error(str(error))
    print(f'Added {count} example recipes to {arguments.username}.')
