import sqlite3

# Connect to the database
conn = sqlite3.connect('student_management.db')
cursor = conn.cursor()

# Check if columns exist before adding them
cursor.execute("PRAGMA table_info(school)")
columns_info = cursor.fetchall()
columns = [column[1] for column in columns_info]

print("Existing columns in school table:", columns)

# Add academic_year column if it doesn't exist
if 'academic_year' not in columns:
    cursor.execute("ALTER TABLE school ADD COLUMN academic_year TEXT DEFAULT '2023-2024' NOT NULL")
    print("Added academic_year column to school table")
else:
    print("academic_year column already exists")

# Add term column if it doesn't exist
if 'term' not in columns:
    cursor.execute("ALTER TABLE school ADD COLUMN term TEXT DEFAULT '1' NOT NULL")
    print("Added term column to school table")
else:
    print("term column already exists")

# Add passing_percentage column if it doesn't exist
if 'passing_percentage' not in columns:
    cursor.execute("ALTER TABLE school ADD COLUMN passing_percentage REAL DEFAULT 40.0 NOT NULL")
    print("Added passing_percentage column to school table")
else:
    print("passing_percentage column already exists")

# Commit the changes and close the connection
conn.commit()
conn.close()

print("Database schema update completed successfully!") 