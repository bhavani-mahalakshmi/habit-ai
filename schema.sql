-- schema.sql

-- Drop existing tables in reverse order of dependency
DROP TABLE IF EXISTS tasks;
DROP TABLE IF EXISTS goals;
DROP TABLE IF EXISTS users;


-- Create the users table (simplified for single user for now)
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    preferences TEXT -- Store JSON string for check-in time etc.
);

-- Create the goals table
CREATE TABLE goals (
    goal_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    description TEXT NOT NULL,
    target_date TEXT, -- Store as TEXT (YYYY-MM-DD) or use specific date type
    status TEXT NOT NULL DEFAULT 'Active', -- e.g., Active, Achieved, Paused
    positive_reasons TEXT NOT NULL, -- Store the 'Top 5 Reasons' text
    consequences_of_inaction TEXT NOT NULL, -- Store the '5 Years...' text
    creation_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (user_id)
);

-- Create the tasks table
CREATE TABLE tasks (
    task_id INTEGER PRIMARY KEY AUTOINCREMENT,
    goal_id INTEGER NOT NULL,
    description TEXT NOT NULL,
    due_date TEXT NOT NULL, -- Store as TEXT (YYYY-MM-DD)
    status TEXT NOT NULL DEFAULT 'Planned', -- e.g., Planned, Completed, Missed
    completion_date TIMESTAMP,
    estimated_time TEXT, -- e.g., "15 minutes", "1 hour"
    creation_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (goal_id) REFERENCES goals (goal_id) ON DELETE CASCADE -- Optional: Delete tasks if goal is deleted
);

-- Add initial default user (important for the app to work as coded)
-- Using INSERT OR IGNORE to prevent errors if the user already exists
INSERT OR IGNORE INTO users (user_id, username, preferences) VALUES (1, 'default_user', '{}');