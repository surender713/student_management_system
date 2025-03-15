import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
from datetime import datetime
from app import db
from app.models import User, Student, Teacher, Admin, Mark, Subject, Class, Attendance, Goal, Exam
from flask_login import login_required, current_user
from flask import redirect, url_for, flash

# Function to generate class rankings
def generate_class_rankings(class_id):
    """
    Generate rankings for students in a specific class based on their overall performance.
    
    Args:
        class_id: ID of the class
        
    Returns:
        DataFrame with student rankings
    """
    # Get all students in the class
    students = Student.query.filter_by(class_id=class_id).all()
    
    # Prepare data for ranking
    ranking_data = []
    
    for student in students:
        # Get all marks for the student
        marks = Mark.query.filter_by(student_id=student.id).all()
        
        if marks:
            # Calculate average percentage
            total_percentage = sum(mark.marks_obtained / mark.total_marks * 100 for mark in marks)
            avg_percentage = total_percentage / len(marks)
            
            # Add to ranking data
            ranking_data.append({
                'student_id': student.id,
                'name': student.full_name,
                'roll_number': student.roll_number,
                'average_percentage': round(avg_percentage, 2)
            })
    
    # Convert to DataFrame and sort by average percentage
    if ranking_data:
        df = pd.DataFrame(ranking_data)
        df = df.sort_values(by='average_percentage', ascending=False)
        df['rank'] = range(1, len(df) + 1)
        return df
    
    return pd.DataFrame()

# Function to generate subject-wise performance analysis
def generate_subject_performance(student_id):
    """
    Generate subject-wise performance analysis for a specific student.
    
    Args:
        student_id: ID of the student
        
    Returns:
        DataFrame with subject performance data
    """
    # Get all marks for the student
    marks = Mark.query.filter_by(student_id=student_id).all()
    
    # Prepare data for analysis
    performance_data = []
    
    for mark in marks:
        subject = Subject.query.get(mark.subject_id)
        exam = Exam.query.get(mark.exam_id)
        
        # Add to performance data
        performance_data.append({
            'subject_id': subject.id,
            'subject_name': subject.name,
            'exam_type': exam.exam_type,
            'marks_obtained': mark.marks_obtained,
            'total_marks': exam.total_marks,
            'percentage': round(mark.marks_obtained / exam.total_marks * 100, 2),
            'date': mark.created_at
        })
    
    # Convert to DataFrame
    if performance_data:
        df = pd.DataFrame(performance_data)
        return df
    
    return pd.DataFrame()

# Function to generate performance trend graph
def generate_performance_trend(student_id):
    """
    Generate performance trend graph for a specific student.
    
    Args:
        student_id: ID of the student
        
    Returns:
        Base64 encoded image of the trend graph
    """
    # Get performance data
    df = generate_subject_performance(student_id)
    
    if df.empty:
        return None
    
    # Group by date and calculate average percentage
    trend_data = df.groupby('date')['percentage'].mean().reset_index()
    trend_data = trend_data.sort_values(by='date')
    
    # Create plot
    plt.figure(figsize=(10, 6))
    plt.plot(trend_data['date'], trend_data['percentage'], marker='o', linestyle='-')
    plt.title('Performance Trend Over Time')
    plt.xlabel('Date')
    plt.ylabel('Average Percentage')
    plt.grid(True)
    plt.tight_layout()
    
    # Save plot to a bytes buffer
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    
    # Encode the image to base64
    image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    plt.close()
    
    return image_base64

# Function to generate top students
def generate_top_students(limit=10):
    """
    Generate a list of top students across all classes.
    
    Args:
        limit: Number of top students to return
        
    Returns:
        DataFrame with top students
    """
    # Get all students
    students = Student.query.all()
    
    # Prepare data for ranking
    ranking_data = []
    
    for student in students:
        # Get all marks for the student
        marks = Mark.query.filter_by(student_id=student.id).all()
        
        if marks:
            # Calculate average percentage
            total_percentage = sum(mark.marks_obtained / mark.total_marks * 100 for mark in marks)
            avg_percentage = total_percentage / len(marks)
            
            # Get class information
            class_info = Class.query.get(student.class_id)
            
            # Add to ranking data
            ranking_data.append({
                'student_id': student.id,
                'name': student.full_name,
                'roll_number': student.roll_number,
                'class': f"{class_info.name} - {class_info.section}",
                'average_percentage': round(avg_percentage, 2)
            })
    
    # Convert to DataFrame and sort by average percentage
    if ranking_data:
        df = pd.DataFrame(ranking_data)
        df = df.sort_values(by='average_percentage', ascending=False)
        df = df.head(limit)
        df['rank'] = range(1, len(df) + 1)
        return df
    
    return pd.DataFrame()

# Function to export student records to CSV
def export_students_to_csv(class_id=None):
    """
    Export student records to CSV.
    
    Args:
        class_id: ID of the class (optional, if None, export all students)
        
    Returns:
        CSV data as string
    """
    # Query students
    if class_id:
        students = Student.query.filter_by(class_id=class_id).all()
    else:
        students = Student.query.all()
    
    # Prepare data for export
    export_data = []
    
    for student in students:
        # Get user information
        user = User.query.get(student.user_id)
        
        # Get class information
        class_info = Class.query.get(student.class_id)
        
        # Add to export data
        export_data.append({
            'id': student.id,
            'full_name': student.full_name,
            'roll_number': student.roll_number,
            'email': user.email,
            'gender': student.gender,
            'date_of_birth': student.date_of_birth,
            'address': student.address,
            'phone': student.phone,
            'parent_name': student.parent_name,
            'parent_phone': student.parent_phone,
            'class': f"{class_info.name} - {class_info.section}",
            'academic_year': class_info.academic_year
        })
    
    # Convert to DataFrame and export to CSV
    if export_data:
        df = pd.DataFrame(export_data)
        return df.to_csv(index=False)
    
    return ""

# Function to check if a user exists
def user_exists(username=None, email=None):
    """
    Check if a user with the given username or email exists.
    
    Args:
        username: Username to check
        email: Email to check
        
    Returns:
        True if user exists, False otherwise
    """
    if username:
        user = User.query.filter_by(username=username).first()
        if user:
            return True
    
    if email:
        user = User.query.filter_by(email=email).first()
        if user:
            return True
    
    return False

# Function to create a default admin user
def create_default_admin(app):
    """
    Create a default admin user if no admin exists.
    
    Args:
        app: Flask application instance
    """
    with app.app_context():
        # Check if admin exists
        admin = User.query.filter_by(role='admin').first()
        
        if not admin:
            from app import bcrypt
            from app.config import Config
            
            # Create admin user
            hashed_password = bcrypt.generate_password_hash(Config.ADMIN_PASSWORD).decode('utf-8')
            admin_user = User(
                username=Config.ADMIN_USERNAME,
                email=Config.ADMIN_EMAIL,
                password=hashed_password,
                role='admin'
            )
            
            db.session.add(admin_user)
            db.session.commit()
            
            # Create admin profile
            admin_profile = Admin(
                user_id=admin_user.id,
                full_name='System Administrator'
            )
            
            db.session.add(admin_profile)
            db.session.commit()
            
            print(f"Default admin user created: {Config.ADMIN_USERNAME}")
        else:
            print("Admin user already exists.")

# Role-specific access decorators
def admin_required(f):
    @login_required
    def decorated_function(*args, **kwargs):
        if current_user.role != 'admin':
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('main.home'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

def teacher_required(f):
    @login_required
    def decorated_function(*args, **kwargs):
        if current_user.role != 'teacher':
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('main.home'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

def student_required(f):
    @login_required
    def decorated_function(*args, **kwargs):
        if current_user.role != 'student':
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('main.home'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function 