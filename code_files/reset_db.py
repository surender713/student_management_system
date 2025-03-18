from app import create_app, db
from app.models import User, Admin, Teacher, Student, Class, School, Subject, Mark, Attendance, Exam, TeacherNote, Question, Answer, Ranking
import os

app = create_app()

def reset_db():
    with app.app_context():
        # Drop all tables
        db.drop_all()
        print("All tables dropped successfully!")
        
        # Create all tables
        db.create_all()
        print("All tables recreated successfully!")

if __name__ == "__main__":
    # Delete the database file if it exists
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'site.db')
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Deleted existing database file: {db_path}")
    
    # Reset the database
    reset_db() 