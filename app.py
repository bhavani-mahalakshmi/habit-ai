# app.py (or your main Flask file)
import sqlite3
from flask import Flask, g # g is a special object for request context

app = Flask(__name__)
DATABASE = 'coach_agent.db' # Make sure this matches

# Function to get a database connection for the current request
def get_db():
    # If 'db' is not in the 'g' object, create a connection
    if 'db' not in g:
        g.db = sqlite3.connect(
            DATABASE,
            detect_types=sqlite3.PARSE_DECLTYPES # Helps with data types
        )
        # Return rows that behave like dictionaries (easier access by column name)
        g.db.row_factory = sqlite3.Row
    return g.db

# Function to close the database connection when the request ends
@app.teardown_appcontext
def close_db(e=None):
    db = g.pop('db', None) # Get the connection from 'g' if it exists
    if db is not None:
        db.close() # Close the connection

# --- Example Usage in a Flask Route (We'll build this out later) ---
@app.route('/')
def index():
    # Example of querying the database
    db = get_db()
    try:
        # Simple example: Count users (should be 0 or 1 initially)
        user_count = db.execute('SELECT COUNT(*) FROM users').fetchone()[0]
        return f"Welcome to your Coach Agent! User count: {user_count}"
    except sqlite3.Error as e:
         return f"Database error: {e}"

# --- (Your other Flask routes will go here) ---

if __name__ == '__main__':
    # Important: Run init_db.py first if the database doesn't exist!
    # You might add a check here or rely on running init_db.py manually.
    app.run(debug=True) # debug=True is helpful during development