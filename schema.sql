CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    vegan INTEGER NOT NULL DEFAULT 0,
    vegetarian INTEGER NOT NULL DEFAULT 0,
    gluten_free INTEGER NOT NULL DEFAULT 0,
    lactose_free INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS recipes (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    rating INTEGER NOT NULL CHECK(rating BETWEEN 0 AND 5),
    cooking_time INTEGER NOT NULL CHECK(cooking_time > 0),
    ingredients TEXT NOT NULL,
    instructions TEXT NOT NULL,
    picture TEXT
);

CREATE TABLE IF NOT EXISTS collections (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    picture TEXT
);

CREATE TABLE IF NOT EXISTS collection_recipes (
    collection_id INTEGER REFERENCES collections(id) ON DELETE CASCADE,
    recipe_id INTEGER REFERENCES recipes(id) ON DELETE CASCADE,
    PRIMARY KEY(collection_id, recipe_id)
);

-- Each row gives an alternative ingredient for one dietary preference.
CREATE TABLE IF NOT EXISTS substitutions (
    id INTEGER PRIMARY KEY,
    ingredient TEXT NOT NULL,
    replacement TEXT NOT NULL,
    diet TEXT NOT NULL CHECK(diet IN ('vegan', 'vegetarian', 'gluten_free', 'lactose_free')),
    UNIQUE(ingredient, diet)
);

-- Default suggestions. Reopening the app does not duplicate these rows.
INSERT OR IGNORE INTO substitutions (ingredient, replacement, diet) VALUES
    ('chicken', 'tofu', 'vegan'),
    ('chicken', 'tofu', 'vegetarian'),
    ('beef', 'tofu', 'vegan'),
    ('beef', 'tofu', 'vegetarian'),
    ('pork', 'tofu', 'vegan'),
    ('pork', 'tofu', 'vegetarian'),
    ('lamb', 'tofu', 'vegan'),
    ('lamb', 'tofu', 'vegetarian'),
    ('turkey', 'tofu', 'vegan'),
    ('turkey', 'tofu', 'vegetarian'),
    ('bacon', 'tofu', 'vegan'),
    ('bacon', 'tofu', 'vegetarian'),
    ('ham', 'tofu', 'vegan'),
    ('ham', 'tofu', 'vegetarian'),
    ('salmon', 'chickpeas', 'vegan'),
    ('salmon', 'chickpeas', 'vegetarian'),
    ('tuna', 'chickpeas', 'vegan'),
    ('tuna', 'chickpeas', 'vegetarian'),
    ('fish', 'chickpeas', 'vegan'),
    ('fish', 'chickpeas', 'vegetarian'),
    ('shrimp', 'chickpeas', 'vegan'),
    ('shrimp', 'chickpeas', 'vegetarian'),
    ('prawns', 'chickpeas', 'vegan'),
    ('prawns', 'chickpeas', 'vegetarian'),
    ('anchovies', 'chickpeas', 'vegan'),
    ('anchovies', 'chickpeas', 'vegetarian'),
    ('egg', 'flax egg (1 tbsp ground flax + 3 tbsp water per egg)', 'vegan'),
    ('eggs', 'flax egg (1 tbsp ground flax + 3 tbsp water per egg)', 'vegan'),
    ('honey', 'maple syrup', 'vegan'),
    ('milk', 'unsweetened plant milk', 'lactose_free'),
    ('milk', 'unsweetened plant milk', 'vegan'),
    ('butter', 'plant-based butter', 'lactose_free'),
    ('butter', 'plant-based butter', 'vegan'),
    ('cheese', 'dairy-free cheese', 'lactose_free'),
    ('cheese', 'dairy-free cheese', 'vegan'),
    ('parmesan', 'dairy-free cheese', 'lactose_free'),
    ('parmesan', 'dairy-free cheese', 'vegan'),
    ('yogurt', 'plant-based yogurt', 'lactose_free'),
    ('yogurt', 'plant-based yogurt', 'vegan'),
    ('yoghurt', 'plant-based yogurt', 'lactose_free'),
    ('yoghurt', 'plant-based yogurt', 'vegan'),
    ('cream', 'oat cream', 'lactose_free'),
    ('cream', 'oat cream', 'vegan'),
    ('wheat flour', 'gluten-free flour blend', 'gluten_free'),
    ('plain flour', 'gluten-free flour blend', 'gluten_free'),
    ('all-purpose flour', 'gluten-free flour blend', 'gluten_free'),
    ('flour', 'gluten-free flour blend', 'gluten_free'),
    ('pasta', 'gluten-free pasta', 'gluten_free'),
    ('spaghetti', 'gluten-free pasta', 'gluten_free'),
    ('noodles', 'gluten-free pasta', 'gluten_free'),
    ('bread', 'gluten-free bread', 'gluten_free'),
    ('soy sauce', 'gluten-free tamari', 'gluten_free'),
    ('breadcrumbs', 'gluten-free breadcrumbs', 'gluten_free');
