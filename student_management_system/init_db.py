from app import create_app, db
from app.models import User, Admin, Teacher, Student, Class, School, Subject, Mark, Attendance, Exam, TeacherNote, Question, Answer, Ranking

app = create_app()

def init_db():
    with app.app_context():
        # Create all tables
        db.create_all()
        print("Database initialized successfully!")

if __name__ == "__main__":
    init_db() 