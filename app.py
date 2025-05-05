# app.py - PART 1: Imports and Configuration
# ==========================================

import sqlite3
from flask import Flask, g, render_template, request, redirect, url_for, flash, get_flashed_messages
import os
import datetime
import google.generativeai as genai # Import Gemini library
from dotenv import load_dotenv # Import dotenv
# Optional: For more detailed error logging
# import traceback

# --- Load Environment Variables ---
load_dotenv() # Load variables from .env file

app = Flask(__name__)
# Use environment variable for secret key or fallback to random bytes for flash messages
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', os.urandom(24))
DATABASE = 'coach_agent.db'
SCHEMA = 'schema.sql'
DEFAULT_USER_ID = 1 # Assuming a single-user setup for now

# --- Configure Gemini API ---
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
GEMINI_CONFIGURED = False
if not GOOGLE_API_KEY:
    print("🔴 WARNING: GOOGLE_API_KEY environment variable not found. AI features will be disabled.")
else:
    try:
        genai.configure(api_key=GOOGLE_API_KEY)
        GEMINI_CONFIGURED = True
        print("✅ Gemini API configured successfully.")
    except Exception as e:
        print(f"🔴 ERROR: Failed to configure Gemini API: {e}")
        print("   AI features will be unavailable.")

# app.py - PART 2: Database Helper Functions
# =========================================
# (Append this code below Part 1)

# --- Database Helper Functions ---
def get_db():
    """Opens a new database connection if there is none yet for the current application context."""
    if 'db' not in g:
        try:
            g.db = sqlite3.connect(DATABASE, detect_types=sqlite3.PARSE_DECLTYPES)
            # Return rows that behave like dicts (access columns by name)
            g.db.row_factory = sqlite3.Row
            print("Database connection opened.")
        except sqlite3.Error as e:
            print(f"🔴 ERROR connecting to database: {e}")
            # Stop the request if DB connection fails
            raise ConnectionError(f"Could not connect to database: {e}") from e
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
    print("Attempting to initialize database if needed...")
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        # Basic check if tables exist (checks for 'users' table)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
        table_exists = cursor.fetchone()
        if not table_exists:
             print(f"Database table 'users' not found. Initializing from {SCHEMA}...")
             try:
                 with open(SCHEMA, 'r') as f:
                     sql_script = f.read()
                 cursor.executescript(sql_script)
                 conn.commit()
                 print(f"✅ Database initialized successfully using {SCHEMA}.")
             except FileNotFoundError:
                 print(f"🔴 ERROR: {SCHEMA} not found. Cannot initialize database.")
             except sqlite3.Error as e:
                 print(f"🔴 ERROR: SQLite error during schema execution: {e}")
        else:
             print("Database tables appear to exist.")
             # Ensure default user exists even if tables are present
             cursor.execute("INSERT OR IGNORE INTO users (user_id, username, preferences) VALUES (?, ?, ?)",
                            (DEFAULT_USER_ID, 'default_user', '{}'))
             conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print(f"🔴 ERROR occurred connecting to or initializing the DB: {e}")

# --- Run DB Initialization Check Once Before First Request ---
# This ensures the DB exists and is initialized before any routes are handled
with app.app_context():
     init_db_command()

# app.py - PART 3: Gemini Helper Function
# ======================================
# (Append this code below Part 2)

# --- Gemini Helper Function ---
def generate_gemini_message(prompt_text):
    """Generates content using the Gemini API."""
    if not GEMINI_CONFIGURED:
        print("Cannot generate response: Gemini API not configured.")
        return "AI features are currently unavailable (API key missing or invalid)."

    try:
        print(f"🧠 Sending prompt to Gemini (first 100 chars): '{prompt_text[:100]}...'")
        model = genai.GenerativeModel('gemini-2.5-flash-preview-04-17')

        # Configure safety settings (optional but recommended)
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        ]

        response = model.generate_content(prompt_text, safety_settings=safety_settings)
        print("✅ Received response from Gemini.")

        # Enhanced response handling
        if response.parts:
            # Ensure we get text content safely
            generated_text = ''.join(part.text for part in response.parts if hasattr(part, 'text'))
            if generated_text:
                return generated_text.strip() # Remove leading/trailing whitespace
            else:
                print("⚠️ Gemini response parts found, but no text content.")
                return "AI Coach message unavailable (Empty response received)."
        # Check for blocking reasons
        elif response.prompt_feedback and response.prompt_feedback.block_reason:
            block_reason = response.prompt_feedback.block_reason
            print(f"⚠️ Gemini content blocked. Reason: {block_reason}")
            return f"AI Coach message blocked (Reason: {block_reason}). Please check content safety guidelines."
        else:
            # Catchall for unknown empty responses
            print(f"⚠️ Gemini response empty or unexpected format. Response: {response}")
            # Log the full response object for deeper debugging if needed
            # print(f"Full Gemini Response Object: {response}")
            return "AI Coach message unavailable (empty or unknown response)."

    except Exception as e:
        print(f"🔴 ERROR calling Gemini API: {e}")
        # Uncomment the line below for a detailed stack trace in the console
        # print(traceback.format_exc())
        return f"AI Coach message unavailable (API Error: Please check server logs)."

def generate_weekly_goals(last_week_goals):
    """
    Generates a list of goals for the week, either randomly or based on the last week's goals.
    If last_week_goals is None, generates random goals.
    If last_week_goals is a string, generates new goals based on it using Gemini.
    """
    goal_descriptions = []
    try:
        db = get_db()
        if last_week_goals is None:
            # Generate random goals
            goal_descriptions = [
                "Dedicate 30 minutes daily to learning a new skill.",
                "Engage in a physical activity for at least 4 days this week.",
                "Read for 20 minutes each day.",
                "Practice meditation for 15 minutes daily.",
                "Complete a personal project milestone.",
            ]
        else:
            # Generate goals based on last_week_goals using Gemini
            prompt = f"""
            Act as a helpful personal coach.
            The user's goals for last week were: "{last_week_goals}".
            Generate 3 SMART (Specific, Measurable, Achievable, Relevant, Time-bound) goals for the user for this coming week, taking into account what they were working on last week.
            Please only return a comma separated list of goals.
            """
            ai_response = generate_gemini_message(prompt)

            # Check if the response is an error message
            if "AI Coach message unavailable" in ai_response or "AI Coach message blocked" in ai_response:
                flash(ai_response, "error")
                return  # Exit if AI response is an error

            goal_descriptions = [goal.strip() for goal in ai_response.split(',') if goal.strip()]
            
            if not goal_descriptions:
                print(f"🔴 ERROR: No goals generated from Gemini response: '{ai_response}'")
                flash(f"Could not generate goals based on previous goals", "error")
                return
        
        # Inserts goals in db
        db = get_db()

        for description in goal_descriptions:
            db.execute(
                "INSERT INTO goals (user_id, description, status, creation_date) VALUES (?, ?, 'Active', CURRENT_TIMESTAMP)",
                (DEFAULT_USER_ID, description)
            )
        db.commit()
        print(f"✅ Weekly goals added to the database.")
        flash("Weekly goals added successfully!", "success")
    except sqlite3.Error as e:
        print(f"🔴 ERROR adding weekly goals to the database: {e}")
        flash(f"Database error adding weekly goals: {e}", "error")
        return
    except Exception as e:
        print(f"🔴 ERROR generating weekly goals: {e}")
        flash(f"Error generating weekly goals: {e}", "error")
        return

@app.route('/generate_new_goals', methods=['POST'])
def generate_new_goals_route():
    """
    Route for generating new goals based on last week's goals.
    Receives last week's goals from a form and calls generate_weekly_goals.
    """
    last_week_goals = request.form.get('last_week_goals')
    generate_weekly_goals(last_week_goals)
    return redirect(url_for('index'))

# --- Function to get last week's goals descriptions ---
def get_last_week_goals_descriptions():
    """Retrieves the descriptions of goals created last week."""
    db = get_db()
    try:
        last_week_goals = db.execute(
            "SELECT description FROM goals WHERE user_id = ? AND creation_date >= date('now', '-7 days') AND creation_date < date('now')",
            (DEFAULT_USER_ID,)
        ).fetchall()
        return ", ".join([goal['description'] for goal in last_week_goals]) if last_week_goals else None
    except sqlite3.Error as e:
        print(f"🔴 Database error fetching last week's goals: {e}")
        flash(f"Error fetching last week's goals: {e}", "error")
        return None
        # print(traceback.format_exc())
        return f"AI Coach message unavailable (API Error: Please check server logs)."

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
        print(f"🔴 Database error fetching goals: {e}")
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
                print(f"🔴 Database error on goal save: {e}")
            except Exception as e:
                flash(f"An unexpected error occurred: {e}", "error")
                print(f"🔴 Unexpected error on goal save: {e}")

    # Handle GET request (or POST with errors - flash message displayed in template)
    return render_template('goal_setup.html')

@app.route('/goal/<int:goal_id>', methods=['GET', 'POST'])
def goal_detail(goal_id):
    """Shows goal details, lists tasks, handles adding tasks, AND gets AI message."""
    db = get_db()
    goal = None
    tasks = []
    ai_message = "AI message generation skipped (not a GET request or goal not found)." # Default

    # Fetch the specific goal
    try:
        goal_cursor = db.execute(
            "SELECT * FROM goals WHERE goal_id = ? AND user_id = ?",
            (goal_id, DEFAULT_USER_ID)
        )
        goal = goal_cursor.fetchone()
    except sqlite3.Error as e:
        print(f"🔴 Error fetching goal {goal_id}: {e}")
        flash(f"Could not fetch goal details: {e}", "error")
        # Redirect immediately if goal fetch fails fundamentally
        return redirect(url_for('index'))

    if goal is None:
         # Only flash if no specific DB error was flashed already
         if not get_flashed_messages(category_filter=["error"]):
              flash("Goal not found or access denied.", "error")
         return redirect(url_for('index')) # Redirect if goal is None after fetch attempt

    # --- Handle Adding a New Task (POST request) ---
    if request.method == 'POST':
        task_description = request.form.get('task_description')
        task_due_date = request.form.get('task_due_date') # Consider date validation

        if not task_description or not task_due_date:
            flash("Task description and due date are required.", "error")
        else:
            try:
                # Ensure DB connection is available (though usually it is from 'db = get_db()' above)
                # db = get_db() # Redundant if already called
                db.execute(
                    "INSERT INTO tasks (goal_id, description, due_date) VALUES (?, ?, ?)",
                    (goal_id, task_description, task_due_date)
                )
                db.commit()
                flash("Task added successfully!", "success")
                # Redirect back to the same page using GET to show the new task and clear form
                return redirect(url_for('goal_detail', goal_id=goal_id))
            except sqlite3.Error as e:
                flash(f"Database error adding task: {e}", "error")
                print(f"🔴 Error adding task for goal {goal_id}: {e}")
                # Fall through to render template again, showing the error message
            except Exception as e:
                 flash(f"An unexpected error occurred while adding task: {e}", "error")
                 print(f"🔴 Unexpected error adding task for goal {goal_id}: {e}")
                 # Fall through to render template

    # --- Fetch existing tasks for this goal (Always done for GET, or after POST if redirect didn't happen) ---
    try:
         tasks_cursor = db.execute(
             "SELECT * FROM tasks WHERE goal_id = ? ORDER BY due_date, status, creation_date",
             (goal_id,)
         )
         tasks = tasks_cursor.fetchall()
    except sqlite3.Error as e:
        flash("Could not fetch tasks.", "error")
        print(f"🔴 Error fetching tasks for goal {goal_id}: {e}")
        # Allow template rendering even if task fetch fails, but show error

    # --- Generate AI Message (Only on GET request AND if goal exists AND API configured) ---
    if request.method == 'GET': # Crucial: Only call API on GET
        if goal and GEMINI_CONFIGURED:
            try:
                # Construct a prompt using the goal's data
                prompt = f"""
                Act as a very brief, supportive coach. Look at the following goal and the user's reasons for achieving it.
                Goal: "{goal['description']}"
                User's Reasons Why: "{goal['positive_reasons']}"

                Based ONLY on the information above, provide a short (1-2 sentences maximum) encouraging message to help this user stay motivated towards their goal today. Do not ask questions. Be positive and direct. Address the user ("You...").
                """
                ai_message = generate_gemini_message(prompt)
            except Exception as e:
                 # Catch potential errors during prompt construction or the call itself
                 print(f"🔴 Error during AI message generation logic: {e}")
                 ai_message = "AI Coach message generation failed."
        elif goal and not GEMINI_CONFIGURED:
            ai_message = "AI features require API configuration."
        else:
             # This case shouldn't typically be hit due to checks above, but included for completeness
             ai_message = "Cannot generate AI message (Goal missing or API issue)."


    # Get today's date for the default due date input in the form
    today_date = datetime.date.today().isoformat()

    # Pass all necessary variables to the template
    return render_template('goal_detail.html', goal=goal, tasks=tasks, today_date=today_date, ai_message=ai_message)

# app.py - PART 5: Task Action Routes & Main Execution
# ==================================================
# (Append this code below Part 4)

# --- Task Action Routes ---
@app.route('/task/<int:task_id>/complete', methods=['POST'])
def mark_task_complete(task_id):
    """Marks a task as Completed."""
    db = get_db()
    goal_id = None # Initialize goal_id to handle potential errors
    try:
        # Verify task belongs to the default user before updating
        task = db.execute("SELECT goal_id FROM tasks WHERE task_id = ? AND goal_id IN (SELECT goal_id FROM goals WHERE user_id = ?)",
                          (task_id, DEFAULT_USER_ID)).fetchone()
        if task:
            goal_id = task['goal_id']
            completion_time = datetime.datetime.now() # Record precise completion time
            db.execute("UPDATE tasks SET status = 'Completed', completion_date = ? WHERE task_id = ?",
                       (completion_time, task_id))
            db.commit()
            flash(f"Task marked as Completed!", "success")
            print(f"Task {task_id} marked complete.")
        else:
            flash("Task not found or not accessible.", "error")

    except sqlite3.Error as e:
        flash(f"Database error updating task: {e}", "error")
        print(f"🔴 DB error completing task {task_id}: {e}")
    except Exception as e:
         flash(f"An unexpected error occurred: {e}", "error")
         print(f"🔴 Unexpected error completing task {task_id}: {e}")

    # Redirect logic: Redirects to goal detail if possible, otherwise index
    if goal_id:
        return redirect(url_for('goal_detail', goal_id=goal_id))
    else:
        # If goal_id couldn't be determined (task not found or error before fetch)
        return redirect(url_for('index'))

@app.route('/task/<int:task_id>/missed', methods=['POST'])
def mark_task_missed(task_id):
    """Marks a task as Missed."""
    db = get_db()
    goal_id = None
    try:
        # Get the goal_id for redirection and verification
        task = db.execute("SELECT goal_id FROM tasks WHERE task_id = ? AND goal_id IN (SELECT goal_id FROM goals WHERE user_id = ?)",
                          (task_id, DEFAULT_USER_ID)).fetchone()
        if task:
            goal_id = task['goal_id']
            # Set status to Missed, clear completion date
            db.execute("UPDATE tasks SET status = 'Missed', completion_date = NULL WHERE task_id = ?", (task_id,))
            db.commit()
            flash(f"Task marked as Missed.", "warning") # Use 'warning' category for missed?
            print(f"Task {task_id} marked missed.")
        else:
            flash("Task not found or not accessible.", "error")

    except sqlite3.Error as e:
        flash(f"Database error updating task: {e}", "error")
        print(f"🔴 DB error marking task {task_id} missed: {e}")
    except Exception as e:
         flash(f"An unexpected error occurred: {e}", "error")
         print(f"🔴 Unexpected error marking task {task_id} missed: {e}")

    # Redirect logic
    if goal_id:
        return redirect(url_for('goal_detail', goal_id=goal_id))
    else:
        return redirect(url_for('index'))

# Generate the weekly goals to populate the db
generate_weekly_goals(None)

# Test generate new goals with the last week goals
last_week_goals_description = get_last_week_goals_descriptions()
generate_weekly_goals(last_week_goals_description)
@app.route('/task/<int:task_id>/reset', methods=['POST'])
def reset_task_status(task_id):
    """Resets a task status back to Planned."""
    db = get_db()
    goal_id = None
    try:
        # Get the goal_id for redirection and verification
        task = db.execute("SELECT goal_id FROM tasks WHERE task_id = ? AND goal_id IN (SELECT goal_id FROM goals WHERE user_id = ?)",
                          (task_id, DEFAULT_USER_ID)).fetchone()
        if task:
            goal_id = task['goal_id']
            # Set status back to Planned, clear completion date
            db.execute("UPDATE tasks SET status = 'Planned', completion_date = NULL WHERE task_id = ?", (task_id,))
            db.commit()
            flash(f"Task status reset to Planned.", "info") # Use 'info' category
            print(f"Task {task_id} status reset.")
        else:
            flash("Task not found or not accessible.", "error")

    except sqlite3.Error as e:
        flash(f"Database error updating task: {e}", "error")
        print(f"🔴 DB error resetting task {task_id}: {e}")
    except Exception as e:
         flash(f"An unexpected error occurred: {e}", "error")
         print(f"🔴 Unexpected error resetting task {task_id}: {e}")

    # Redirect logic
    if goal_id:
        return redirect(url_for('goal_detail', goal_id=goal_id))
    else:
        return redirect(url_for('index'))

# --- Main execution ---
if __name__ == '__main__':
    print("Starting Flask application...")
    # Ensure the DB init check runs if using the @app.before_first_request approach,
    # otherwise, make sure init_db_command() was run manually or via init_db.py
    app.run(debug=True, host='0.0.0.0', port=5001) # Makes it accessible on local network, debug=True is helpful for development
