"""
Script to add missing columns to test_sessions table
Run this to update the database schema without losing data
"""
import sqlite3
import os

# Path to database
db_path = "c:/Users/sonuk/OneDrive/Desktop/Interview/interview_new/backend/interview.db"

if not os.path.exists(db_path):
    print("Database not found!")
    exit(1)

# Connect to database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("Adding new columns to test_sessions table...")

try:
    # Add candidate_name column
    cursor.execute("ALTER TABLE test_sessions ADD COLUMN candidate_name VARCHAR")
    print("✅ Added candidate_name column")
except sqlite3.OperationalError as e:
    print(f"⚠️ candidate_name: {e}")

try:
    # Add candidate_email column
    cursor.execute("ALTER TABLE test_sessions ADD COLUMN candidate_email VARCHAR")
    print("✅ Added candidate_email column")
except sqlite3.OperationalError as e:
    print(f"⚠️ candidate_email: {e}")

try:
    # Add candidate_mobile column
    cursor.execute("ALTER TABLE test_sessions ADD COLUMN candidate_mobile VARCHAR")
    print("✅ Added candidate_mobile column")
except sqlite3.OperationalError as e:
    print(f"⚠️ candidate_mobile: {e}")

try:
    # Add test_date column
    cursor.execute("ALTER TABLE test_sessions ADD COLUMN test_date VARCHAR")
    print("✅ Added test_date column")
except sqlite3.OperationalError as e:
    print(f"⚠️ test_date: {e}")

try:
    # Add batch_time column
    cursor.execute("ALTER TABLE test_sessions ADD COLUMN batch_time VARCHAR")
    print("✅ Added batch_time column")
except sqlite3.OperationalError as e:
    print(f"⚠️ batch_time: {e}")

# Commit changes
conn.commit()
conn.close()

print("\n✅ Database schema updated successfully!")
print("You can now restart the backend server.")
