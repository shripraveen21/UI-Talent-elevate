import sqlite3

# Connect to the database
conn = sqlite3.connect('mockdata.db')
cursor = conn.cursor()

# Get all table names
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print("Tables in database:")
for table in tables:
    print(f"  - {table[0]}")

# Check employees table structure
print("\nEmployees table structure:")
cursor.execute("PRAGMA table_info(employees);")
columns = cursor.fetchall()
for col in columns:
    print(f"  {col[1]} ({col[2]})")

# Check sample employee data
print("\nSample employee data:")
cursor.execute("SELECT user_id, name, band, tech_stack FROM employees LIMIT 5;")
employees = cursor.fetchall()
for emp in employees:
    print(f"  ID: {emp[0]}, Name: {emp[1]}, Band: {emp[2]}, Tech Stack: {emp[3]}")

# Check if employee_skills table exists
print("\nEmployee Skills table:")
try:
    cursor.execute("SELECT * FROM employee_skills LIMIT 5;")
    skills = cursor.fetchall()
    print(f"Found {len(skills)} skill records")
    for skill in skills:
        print(f"  {skill}")
except sqlite3.OperationalError as e:
    print(f"  Error: {e}")

conn.close()