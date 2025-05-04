# app.py
import sqlite3
from flask import Flask, g, render_template, request, redirect, url_for, flash
import os
import datetime

app = Flask(__name__)
# Secret key is needed for flashing messages
app.config['SECRET_KEY'] = os.urandom(24) # Replace with a fixed secret key in production
DATABASE = 'coach_agent.db'
SCHEMA = 'schema.sql'
DEFAULT_USER_ID = 1 # Assuming a single-user setup for now

# --- Database Helper Functions ---

def get_db():
    """Opens a new database connection if there is none yet for the current application context."""
    if 'db' not in g:
        try:
            g.db = sqlite3.connect(DATABASE, detect_types=sqlite3.PARSE_DECLTYPES)
            g.db.row_factory = sqlite3.Row # Return rows that behave like dicts
            print("Database connection opened.")
        except sqlite3.Error as e:
            print(f"Error connecting to database: {e}")
            # Handle error appropriately, maybe raise it or return None
            raise e # Or handle more gracefully
    return g.db

@app.teardown_appcontext
def close_db(e=None):
    """Closes the database again at the end of the request."""
    db = g.pop('db', None)
    if db is not None:
        db.close()
        print("Database connection closed.")

def init_db_command():
    """Helper to initialize DB from schema file if it doesn't exist or is empty."""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        # Basic check if tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('users', 'goals', 'tasks');")
        tables = cursor.fetchall()
        if len(tables) < 3: # If not all tables exist
             print(f"Database tables missing or incomplete. Initializing from {SCHEMA}...")
             try:
                 with open(SCHEMA, 'r') as f:
                     sql_script = f.read()
                 cursor.executescript(sql_script)
                 conn.commit()
                 print(f"Database initialized successfully using {SCHEMA}.")
             except FileNotFoundError:
                 print(f"ERROR: {SCHEMA} not found. Cannot initialize database.")
             except sqlite3.Error as e:
                 print(f"ERROR: SQLite error during schema execution: {e}")
        else:
             print("Database tables already exist.")
             # Ensure default user exists
             cursor.execute("INSERT OR IGNORE INTO users (user_id, username, preferences) VALUES (?, ?, ?)",
                            (DEFAULT_USER_ID, 'default_user', '{}'))
             conn.commit()

        conn.close()
    except sqlite3.Error as e:
        print(f"An error occurred connecting to or initializing the DB: {e}")

# --- Ensure DB exists on first request ---
@app.before_request
def before_request():
    # Simple check, could be more robust
    if not os.path.exists(DATABASE):
        print(f"{DATABASE} not found, attempting to initialize.")
        init_db_command()
    elif os.path.getsize(DATABASE) == 0: # Check if empty file
        print(f"{DATABASE} found but is empty, attempting to initialize.")
        init_db_command()
    else:
        # Optionally ensure default user exists on every startup if DB exists
        try:
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            cursor.execute("INSERT OR IGNORE INTO users (user_id, username, preferences) VALUES (?, ?, ?)",
                           (DEFAULT_USER_ID, 'default_user', '{}'))
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
             print(f"Error ensuring default user exists: {e}")


# --- Routes ---

@app.route('/')
def index():
    """Main dashboard showing active goals."""
    db = get_db()
    goals = []
    try:
        goals_cursor = db.execute(
            "SELECT goal_id, description, status FROM goals WHERE user_id = ? AND status = 'Active' ORDER BY creation_date DESC",
            (DEFAULT_USER_ID,)
        )
        goals = goals_cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Database error fetching goals: {e}")
        flash(f"Error fetching goals: {e}", "error")

    return render_template('index.html', goals=goals)

@app.route('/setup_goal', methods=['GET', 'POST'])
def setup_goal():
    """Displays form to set up a goal and handles submission."""
    if request.method == 'POST':
        description = request.form.get('description')
        target_date = request.form.get('target_date') # Optional field
        positive_reasons = request.form.get('positive_reasons')
        consequences = request.form.get('consequences')

        if not description or not positive_reasons or not consequences:
            flash('Goal description, positive reasons, and consequences are required.', 'error')
        else:
            try:
                db = get_db()
                db.execute(
                    '''INSERT INTO goals (user_id, description, target_date, positive_reasons, consequences_of_inaction)
                       VALUES (?, ?, ?, ?, ?)''',
                    (DEFAULT_USER_ID, description, target_date if target_date else None, positive_reasons, consequences)
                )
                db.commit()
                print(f"Goal '{description}' saved successfully.")
                flash('Goal saved successfully!', 'success')
                return redirect(url_for('index')) # Redirect to dashboard after saving

            except sqlite3.Error as e:
                flash(f"Database error saving goal: {e}", "error")
                print(f"Database error on goal save: {e}")
            except Exception as e:
                flash(f"An unexpected error occurred: {e}", "error")
                print(f"Unexpected error on goal save: {e}")

    # Handle GET request (or POST with errors - flash handles displaying them)
    return render_template('goal_setup.html')


@app.route('/goal/<int:goal_id>', methods=['GET', 'POST'])
def goal_detail(goal_id):
    """Shows goal details, lists tasks, and handles adding new tasks."""
    db = get_db()
    goal = None
    tasks = []

    # Fetch the specific goal
    try:
        goal_cursor = db.execute(
            "SELECT * FROM goals WHERE goal_id = ? AND user_id = ?",
            (goal_id, DEFAULT_USER_ID)
        )
        goal = goal_cursor.fetchone()
    except sqlite3.Error as e:
        print(f"Error fetching goal {goal_id}: {e}")
        flash(f"Could not fetch goal details: {e}", "error")

    if goal is None:
         flash("Goal not found or access denied.", "error")
         return redirect(url_for('index')) # Redirect if goal not found

    # Handle Adding a New Task (POST request)
    if request.method == 'POST':
        task_description = request.form.get('task_description')
        task_due_date = request.form.get('task_due_date') # Should ideally be validated

        if not task_description or not task_due_date:
            flash("Task description and due date are required.", "error")
        else:
            try:
                db.execute(
                    "INSERT INTO tasks (goal_id, description, due_date) VALUES (?, ?, ?)",
                    (goal_id, task_description, task_due_date)
                )
                db.commit()
                print(f"Task '{task_description}' added for goal {goal_id}")
                flash("Task added successfully!", "success")
                # Redirect back to the same page to show the new task and clear form
                return redirect(url_for('goal_detail', goal_id=goal_id))
            except sqlite3.Error as e:
                print(f"Error adding task for goal {goal_id}: {e}")
                flash(f"Database error adding task: {e}", "error")

    # Fetch existing tasks for this goal (for GET request or after POST error)
    try:
         tasks_cursor = db.execute(
             "SELECT * FROM tasks WHERE goal_id = ? ORDER BY due_date, status, creation_date",
             (goal_id,)
         )
         tasks = tasks_cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Error fetching tasks for goal {goal_id}: {e}")
        flash("Could not fetch tasks.", "error")

    # Get today's date for the default due date input
    today_date = datetime.date.today().isoformat() # YYYY-MM-DD format

    return render_template('goal_detail.html', goal=goal, tasks=tasks, today_date=today_date)


# --- Simple success page route (No longer needed if flashing/redirecting) ---
# @app.route('/goal_saved')
# def goal_saved_success():
#     return "Goal saved successfully! <a href='/'>Go to Dashboard</a>"


# --- Main execution ---
if __name__ == '__main__':
    print("Starting Flask application...")
    # Run init_db_command once explicitly before starting if needed,
    # or rely on the before_request handler.
    # init_db_command() # Optional: Ensure DB is checked/created before first request
    app.run(debug=True) # debug=True reloads on code change and shows errors in browser