
-- other query for the users table
DROP TABLE IF EXISTS users;
CREATE TABLE users
(
    username TEXT PRIMARY KEY,
    password TEXT NOT NULL
);

DROP TABLE IF EXISTS recipes;
CREATE TABLE recipes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    title TEXT NOT NULL,
    ingredients TEXT NOT NULL,
    steps TEXT NOT NULL,
    image_path TEXT,
    allergies TEXT NOT NULL, 
    type TEXT,
    FOREIGN KEY (username) REFERENCES users(id)
);
-- type - breakfast, lunch, dinner, snack

DROP TABLE IF EXISTS reviews;
CREATE TABLE reviews(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recipe_id INTEGER NOT NULL,
    username TEXT NOT NULL,
    feedback TEXT NOT NULL,
    score REAL NOT NULL,
    FOREIGN KEY (id) REFERENCES recipes(recipe_id)
);


SELECT * FROM recipes;

SELECT users.username AS publisher
FROM recipes
JOIN users ON recipes.username = users.username
WHERE recipes.id = '2';