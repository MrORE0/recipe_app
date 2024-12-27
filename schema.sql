PRAGMA encoding = "UTF-8";
PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS users;
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
);
DROP TABLE IF EXISTS recipes;
CREATE TABLE IF NOT EXISTS recipes (
    id TEXT PRIMARY KEY,
    username TEXT NOT NULL,
    title TEXT NOT NULL,
    ingredients TEXT NOT NULL,
    steps TEXT NOT NULL,
    image_path TEXT,
    allergies TEXT,
    type TEXT,
    FOREIGN KEY (username) REFERENCES users(id)
);

-- Insert default admin user if not exists
INSERT OR IGNORE INTO users (id, username, password)
VALUES ('admin_default_id', 'admin', 'scrypt:32768:8:1$verySecureHash');

DROP TABLE IF EXISTS reviews;
CREATE TABLE reviews(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recipe_id INTEGER NOT NULL,
    username TEXT NOT NULL,
    feedback TEXT NOT NULL,
    score REAL NOT NULL,
    FOREIGN KEY (id) REFERENCES recipes(recipe_id)
);

DROP TABLE IF EXISTS favourites;
CREATE TABLE favourites (
    username TEXT NOT NULL,
    recipe_id INTEGER NOT NULL,
    FOREIGN KEY (recipe_id) REFERENCES recipes(id),
    FOREIGN KEY (username) REFERENCES users(username)
);

SELECT * FROM recipes;


SELECT r.username AS username FROM recipes as r
        JOIN favourites AS f ON r.id = f.recipe_id
        JOIN users AS u ON f.username = u.username
        WHERE id = 1;


