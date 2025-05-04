# init_db.py
import sqlite3
import os

DATABASE = 'coach_agent.db' # Name of your database file
SCHEMA = 'schema.sql'

def init_db():
    print(f"Looking for database '{DATABASE}' and schema '{SCHEMA}'...")
    db_exists = os.path.exists(DATABASE)

    try:
        # Connect to the database (creates the file if it doesn't exist)
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        print(f"Connected to '{DATABASE}'.")

        # Read the schema file
        print(f"Reading schema from '{SCHEMA}'...")
        with open(SCHEMA, 'r') as f:
            sql_script = f.read()

        # Execute the SQL script (can contain multiple statements)
        print("Executing schema script...")
        cursor.executescript(sql_script)

        print("Database schema applied successfully.")

        # Commit changes and close connection
        conn.commit()
        conn.close()
        print("Database connection closed.")

    except sqlite3.Error as e:
        print(f"An SQLite error occurred: {e}")
    except FileNotFoundError:
        print(f"Error: {SCHEMA} not found in the current directory.")
        print("Please ensure schema.sql is in the same folder as this script.")
    except Exception as e:
         print(f"An unexpected error occurred: {e}")

if __name__ == '__main__':
    init_db()