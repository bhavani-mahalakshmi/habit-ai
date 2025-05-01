# app.py (add these imports at the top if not already present)
from flask import Flask, g, render_template, request, redirect, url_for
import sqlite3
import os # To check if DB exists

app = Flask(__name__)
DATABASE = 'coach_agent.db'

# --- get_db() and close_db() functions from previous step ---
def get_db():
    # ... (same as before) ...
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE, detect_types=sqlite3.PARSE_DECLTYPES)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(e=None):
    # ... (same as before) ...
    db = g.pop('db', None)
    if db is not None:
        db.close()

# --- Function to ensure DB exists and has a default user ---
def check_or_init_db():
    if not os.path.exists(DATABASE):
        print(f"Database {DATABASE} not found. Running init_db...")
        # You might need to adjust how you call init_db depending on your project structure
        # For simplicity, let's assume init_db() is defined here or imported
        # from init_db import init_db
        # init_db()
        # Or, simpler for now, just create the DB and add the user if it's missing
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        try:
            # Check if schema needs creating (basic check for users table)
             cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
             if cursor.fetchone() is None:
                 print("Tables not found, running schema...")
                 with open('schema.sql', 'r') as f:
                     sql_script = f.read()
                 cursor.executescript(sql_script)
                 print("Schema applied.")
                 # Add default user if tables were just created
                 print("Adding default user...")
                 cursor.execute("INSERT INTO users (username, preferences) VALUES (?, ?)", ('default_user', '{}'))
                 conn.commit()
                 print("Default user added.")
             else:
                 # Ensure default user exists even if tables are present
                 cursor.execute("INSERT OR IGNORE INTO users (username, preferences) VALUES (?, ?)", ('default_user', '{}'))
                 conn.commit()

        except Exception as e:
             print(f"Error during DB check/init: {e}")
        finally:
            conn.close()

# --- Route for setting up a new goal ---
@app.route('/setup_goal', methods=['GET', 'POST'])
def setup_goal():
    check_or_init_db() # Ensure DB and user exist before proceeding
    error = None
    if request.method == 'POST':
        # --- Data Extraction ---
        description = request.form.get('description')
        target_date = request.form.get('target_date') # Optional field
        positive_reasons = request.form.get('positive_reasons')
        consequences = request.form.get('consequences')

        # --- Basic Validation ---
        if not description or not positive_reasons or not consequences:
            error = 'Goal description, positive reasons, and consequences are required.'
        else:
            try:
                db = get_db()
                # For simplicity, assume we always use user_id 1 (the default user)
                # In a real app, you'd get the logged-in user's ID
                default_user_id = 1

                # --- SQL Insertion ---
                db.execute(
                    '''INSERT INTO goals (user_id, description, target_date, positive_reasons, consequences_of_inaction)
                       VALUES (?, ?, ?, ?, ?)''',
                    (default_user_id, description, target_date if target_date else None, positive_reasons, consequences)
                )
                db.commit()
                print(f"Goal '{description}' saved successfully.")
                # --- Redirection ---
                # Redirect to a simple success page or the main dashboard (index for now)
                return redirect(url_for('goal_saved_success')) # Redirect to avoid form resubmission

            except sqlite3.Error as e:
                error = f"Database error: {e}"
                print(f"Database error on goal save: {e}")
            except Exception as e:
                error = f"An unexpected error occurred: {e}"
                print(f"Unexpected error on goal save: {e}")

    # --- Handle GET request (or POST with errors) ---
    # Render the form page
    return render_template('goal_setup.html', error=error)

# --- Simple success page route ---
@app.route('/goal_saved')
def goal_saved_success():
    return "Goal saved successfully! <a href='/'>Go to Dashboard</a>" # Replace with link to actual dashboard later

# --- Your main index route (example) ---
@app.route('/')
def index():
    check_or_init_db()
    # Later, we'll fetch goals and tasks here to display them
    return "Welcome to your Coach Agent Dashboard! <a href='/setup_goal'>Set up a new goal</a>"

if __name__ == '__main__':
    app.run(debug=True)