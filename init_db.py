# init_db.py
import sqlite3

DATABASE = 'coach_agent.db' # Name of your database file

def init_db():
    print("Initializing the database...")
    try:
        # Connect to the database (creates the file if it doesn't exist)
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        # Read the schema file
        with open('schema.sql', 'r') as f:
            sql_script = f.read()

        # Execute the SQL script (can contain multiple statements)
        cursor.executescript(sql_script)

        print("Database schema created successfully.")

        # Commit changes and close connection
        conn.commit()
        conn.close()
        print("Database connection closed.")

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
    except FileNotFoundError:
        print("Error: schema.sql not found in the current directory.")
    except Exception as e:
         print(f"An unexpected error occurred: {e}")

if __name__ == '__main__':
    init_db()