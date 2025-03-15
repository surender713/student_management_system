from datetime import datetime
from flask_login import UserMixin
from app import db, login_manager

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# School model
class School(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.Text)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    website = db.Column(db.String(120))
    academic_year = db.Column(db.String(20), nullable=False, default="2023-2024")
    term = db.Column(db.String(20), nullable=False, default="1")
    passing_percentage = db.Column(db.Float, nullable=False, default=40.0)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    admins = db.relationship('Admin', backref='school', lazy=True)
    teachers = db.relationship('Teacher', backref='school', lazy=True)
    students = db.relationship('Student', backref='school', lazy=True)
    classes = db.relationship('Class', backref='school', lazy=True)
    
    def __repr__(self):
        return f"School('{self.name}')"

# User model for authentication
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='student')  # 'admin', 'teacher', 'student'
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    admin_profile = db.relationship('Admin', backref='user', uselist=False, cascade="all, delete-orphan")
    teacher_profile = db.relationship('Teacher', backref='user', uselist=False, cascade="all, delete-orphan")
    student_profile = db.relationship('Student', backref='user', uselist=False, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.role}')"

# Admin model
class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    is_super_admin = db.Column(db.Boolean, default=False)  # Super admin can manage all schools
    school_id = db.Column(db.Integer, db.ForeignKey('school.id'))
    
    def __repr__(self):
        return f"Admin('{self.full_name}')"

# Admin Request model
class AdminRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    school_id = db.Column(db.Integer, db.ForeignKey('school.id'), nullable=False)
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')  # 'pending', 'approved', 'rejected'
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    school = db.relationship('School', backref='admin_requests', lazy=True)
    
    def __repr__(self):
        return f"AdminRequest('{self.full_name}', '{self.email}', '{self.status}')"

# Teacher model
class Teacher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    qualification = db.Column(db.String(100))
    department = db.Column(db.String(100))
    experience = db.Column(db.String(20))
    category = db.Column(db.String(20), default='TGT')  # PRT, TGT, PGT
    subject_specialization = db.Column(db.String(100))
    school_id = db.Column(db.Integer, db.ForeignKey('school.id'))
    join_date = db.Column(db.Date, default=datetime.utcnow().date())
    
    # Relationships
    classes = db.relationship('Class', backref='teacher', lazy=True)
    subjects = db.relationship('Subject', backref='teacher', lazy=True)
    notes = db.relationship('TeacherNote', backref='teacher', lazy=True)
    exams = db.relationship('Exam', backref='teacher', lazy=True)
    
    def __repr__(self):
        return f"Teacher('{self.full_name}')"

# Student model
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    roll_number = db.Column(db.String(20), unique=True, nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    address = db.Column(db.Text)
    phone = db.Column(db.String(20))
    parent_name = db.Column(db.String(100))
    parent_phone = db.Column(db.String(20))
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False)
    school_id = db.Column(db.Integer, db.ForeignKey('school.id'))
    
    # Relationships
    marks = db.relationship('Mark', backref='student', lazy=True, cascade="all, delete-orphan")
    attendance = db.relationship('Attendance', backref='student', lazy=True, cascade="all, delete-orphan")
    goals = db.relationship('Goal', backref='student', lazy=True, cascade="all, delete-orphan")
    questions = db.relationship('Question', backref='student', lazy=True)
    
    def __repr__(self):
        return f"Student('{self.full_name}', '{self.roll_number}')"

# Class model
class Class(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    section = db.Column(db.String(10), nullable=False)
    stream = db.Column(db.String(50))  # For 11th and 12th: Science, Commerce, Arts
    academic_year = db.Column(db.String(20), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=False)
    school_id = db.Column(db.Integer, db.ForeignKey('school.id'))
    
    # Relationships
    students = db.relationship('Student', backref='class', lazy=True)
    subjects = db.relationship('Subject', backref='class', lazy=True)
    exams = db.relationship('Exam', backref='class', lazy=True)
    
    def __repr__(self):
        if self.stream:
            return f"Class('{self.name}', '{self.section}', '{self.stream}', '{self.academic_year}')"
        return f"Class('{self.name}', '{self.section}', '{self.academic_year}')"

# Subject model
class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), nullable=False)
    description = db.Column(db.Text)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=False)
    
    # Relationships
    marks = db.relationship('Mark', backref='subject', lazy=True, cascade="all, delete-orphan")
    notes = db.relationship('TeacherNote', backref='subject', lazy=True)
    exams = db.relationship('Exam', backref='subject', lazy=True)
    
    def __repr__(self):
        return f"Subject('{self.name}', '{self.code}')"

# Exam model
class Exam(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    exam_type = db.Column(db.String(50), nullable=False)  # 'midterm', 'final', 'quiz', etc.
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=False)
    total_marks = db.Column(db.Float, nullable=False)
    passing_marks = db.Column(db.Float, nullable=False)
    exam_date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(20), nullable=False, default='upcoming')  # 'upcoming', 'ongoing', 'completed'
    
    # Relationships
    marks = db.relationship('Mark', backref='exam', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"Exam('{self.title}', '{self.exam_type}', '{self.exam_date}')"

# Mark model
class Mark(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    exam_id = db.Column(db.Integer, db.ForeignKey('exam.id'), nullable=False)
    marks_obtained = db.Column(db.Float, nullable=False)
    remarks = db.Column(db.Text)
    submitted_by = db.Column(db.String(20), nullable=False, default='teacher')  # 'teacher' or 'student'
    status = db.Column(db.String(20), nullable=False, default='pending')  # 'pending', 'approved', 'rejected'
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"Mark('{self.student_id}', '{self.subject_id}', '{self.exam_id}', '{self.marks_obtained}')"

# Attendance model
class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date())
    status = db.Column(db.String(20), nullable=False)  # 'present', 'absent', 'late'
    
    def __repr__(self):
        return f"Attendance('{self.student_id}', '{self.date}', '{self.status}')"

# Goal model for student goal setting
class Goal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    target_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='in_progress')  # 'in_progress', 'completed', 'missed'
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    def __repr__(self):
        return f"Goal('{self.student_id}', '{self.title}', '{self.status}')"

# Teacher Note model for sharing notes with students
class TeacherNote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    def __repr__(self):
        return f"TeacherNote('{self.teacher_id}', '{self.subject_id}', '{self.title}')"

# Question model for Q&A section
class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'))
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='open')  # 'open', 'answered', 'closed'
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    answers = db.relationship('Answer', backref='question', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"Question('{self.student_id}', '{self.title}', '{self.status}')"

# Answer model for Q&A section
class Answer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='answers')
    
    def __repr__(self):
        return f"Answer('{self.question_id}', '{self.user_id}')"

# Ranking model for storing student rankings
class Ranking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False)
    school_id = db.Column(db.Integer, db.ForeignKey('school.id'), nullable=False)
    academic_year = db.Column(db.String(20), nullable=False)
    term = db.Column(db.String(20), nullable=False)  # 'first', 'second', 'third', etc.
    total_marks = db.Column(db.Float, nullable=False)
    percentage = db.Column(db.Float, nullable=False)
    class_rank = db.Column(db.Integer, nullable=False)
    school_rank = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    student = db.relationship('Student', backref='rankings')
    class_ = db.relationship('Class', backref='rankings')
    school = db.relationship('School', backref='rankings')
    
    def __repr__(self):
        return f"Ranking('{self.student_id}', '{self.class_id}', '{self.school_id}', '{self.class_rank}', '{self.school_rank}')" 