import sqlite3

# Path to the SQLite database
db_path = "instance/medicalspy.db"

try:
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Fetch all table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    if tables:
        print("Tables in the database:")
        for table in tables:
            print(f"- {table[0]}")
    else:
        print("No tables found in the database.")

except sqlite3.Error as e:
    print(f"Error accessing the database: {e}")

finally:
    if conn:
        conn.close()
