DROP TABLE IF EXISTS gigs;
CREATE TABLE gigs
(
    gig_id INTEGER PRIMARY KEY AUTOINCREMENT, 
    band TEXT NOT NULL, 
    gig_date TEXT NOT NULL
);
INSERT INTO gigs (band, gig_date)
VALUES ('Decaying Shroom', '2024-01-12'),
('Belated Tonic', '2024-01-21'),
('Dumpy Tension of the Divided Unicorn', '2024-02-10'), 
('Belated Tonic', '2024-02-20'),
('Missing Roller and the Earl', '2024-02-26'), 
('Glam Blizzard', '2024-03-07'), 
('Piscatory Classroom', '2024-03-12'),
('Prickly Muse', '2024-03-20'),
('Interactive Children of the Phony Filth', '2024-03-29');

-- other query for the users table
DROP TABLE IF EXISTS users;
CREATE TABLE users
(
    username TEXT PRIMARY KEY,
    password TEXT NOT NULL
);

SELECT * FROM users;