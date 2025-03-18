import sqlite3
import os

# Path to the database file
db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'instance', 'site.db')

def upgrade():
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if the columns already exist
        cursor.execute("PRAGMA table_info(teacher)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Add category column if it doesn't exist
        if 'category' not in columns:
            cursor.execute("""
                ALTER TABLE teacher 
                ADD COLUMN category VARCHAR(20) DEFAULT 'TGT'
            """)
            print("Added category column to teacher table")
        
        # Add subject_specialization column if it doesn't exist
        if 'subject_specialization' not in columns:
            cursor.execute("""
                ALTER TABLE teacher 
                ADD COLUMN subject_specialization VARCHAR(100)
            """)
            print("Added subject_specialization column to teacher table")
        
        # Check if the stream column exists in the class table
        cursor.execute("PRAGMA table_info(class)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Add stream column if it doesn't exist
        if 'stream' not in columns:
            cursor.execute("""
                ALTER TABLE class
                ADD COLUMN stream VARCHAR(50)
            """)
            print("Added stream column to class table")
        
        conn.commit()
        print("Migration completed successfully!")
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
    finally:
        conn.close()

def downgrade():
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Create a new Teacher table without the columns
        cursor.execute("""
            CREATE TABLE teacher_new (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                full_name VARCHAR(100) NOT NULL,
                phone VARCHAR(20),
                qualification VARCHAR(100),
                department VARCHAR(100),
                experience VARCHAR(20),
                school_id INTEGER,
                join_date DATE,
                FOREIGN KEY (user_id) REFERENCES user (id),
                FOREIGN KEY (school_id) REFERENCES school (id)
            )
        """)
        
        # Copy data to the new table
        cursor.execute("""
            INSERT INTO teacher_new
            SELECT id, user_id, full_name, phone, qualification, department, experience, school_id, join_date
            FROM teacher
        """)
        
        # Drop the old table and rename the new one
        cursor.execute("DROP TABLE teacher")
        cursor.execute("ALTER TABLE teacher_new RENAME TO teacher")
        
        # Create a new Class table without the stream column
        cursor.execute("""
            CREATE TABLE class_new (
                id INTEGER PRIMARY KEY,
                name VARCHAR(50) NOT NULL,
                section VARCHAR(10) NOT NULL,
                academic_year VARCHAR(20) NOT NULL,
                teacher_id INTEGER NOT NULL,
                school_id INTEGER,
                FOREIGN KEY (teacher_id) REFERENCES teacher (id),
                FOREIGN KEY (school_id) REFERENCES school (id)
            )
        """)
        
        # Copy data to the new table
        cursor.execute("""
            INSERT INTO class_new
            SELECT id, name, section, academic_year, teacher_id, school_id
            FROM class
        """)
        
        # Drop the old table and rename the new one
        cursor.execute("DROP TABLE class")
        cursor.execute("ALTER TABLE class_new RENAME TO class")
        
        conn.commit()
        print("Downgrade completed successfully!")
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    upgrade() 