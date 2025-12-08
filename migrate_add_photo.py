import sqlite3

# Connect to database
conn = sqlite3.connect('createqr.db')
cursor = conn.cursor()

# Check if photo column exists
cursor.execute("PRAGMA table_info(students)")
columns = [column[1] for column in cursor.fetchall()]

if 'photo' not in columns:
    print("Adding photo column to students table...")
    cursor.execute("ALTER TABLE students ADD COLUMN photo BLOB")
    conn.commit()
    print("Photo column added successfully!")
else:
    print("Photo column already exists.")

# Verify the column was added
cursor.execute("PRAGMA table_info(students)")
print("\nCurrent table schema:")
for col in cursor.fetchall():
    print(f"  {col[1]} ({col[2]})")

conn.close()
