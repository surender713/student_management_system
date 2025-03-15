from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import User, Teacher, Student, Class, Subject, Mark, Attendance, Exam, TeacherNote, Question, Answer
from app.utils import generate_class_rankings, generate_subject_performance, teacher_required
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, FloatField, DateField, SubmitField, PasswordField, TextAreaField
from wtforms.validators import DataRequired, NumberRange, Email, Length, EqualTo, ValidationError
import datetime
from app import bcrypt
from app.utils import user_exists

# Create blueprint
teacher = Blueprint('teacher', __name__)

# Forms
class AddMarkForm(FlaskForm):
    student_id = SelectField('Student', coerce=int, validators=[DataRequired()])
    subject_id = SelectField('Subject', coerce=int, validators=[DataRequired()])
    exam_type = SelectField('Exam Type', choices=[
        ('quiz', 'Quiz'),
        ('assignment', 'Assignment'),
        ('midterm', 'Midterm'),
        ('final', 'Final')
    ], validators=[DataRequired()])
    marks_obtained = FloatField('Marks Obtained', validators=[DataRequired(), NumberRange(min=0)])
    total_marks = FloatField('Total Marks', validators=[DataRequired(), NumberRange(min=1)])
    date = DateField('Date', validators=[DataRequired()], default=datetime.datetime.utcnow)
    submit = SubmitField('Add Mark')

class AddAttendanceForm(FlaskForm):
    student_id = SelectField('Student', coerce=int, validators=[DataRequired()])
    date = DateField('Date', validators=[DataRequired()], default=datetime.datetime.utcnow)
    status = SelectField('Status', choices=[
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late')
    ], validators=[DataRequired()])
    submit = SubmitField('Add Attendance')

# Add Student Form
class AddStudentForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    full_name = StringField('Full Name', validators=[DataRequired()])
    roll_number = StringField('Roll Number', validators=[DataRequired()])
    date_of_birth = DateField('Date of Birth', validators=[DataRequired()])
    gender = SelectField('Gender', choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')], validators=[DataRequired()])
    address = TextAreaField('Address')
    phone = StringField('Phone Number')
    parent_name = StringField('Parent Name')
    parent_phone = StringField('Parent Phone')
    class_id = SelectField('Class', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Add Student')
    
    def validate_username(self, username):
        if user_exists(username=username.data):
            raise ValidationError('That username is already taken. Please choose a different one.')
    
    def validate_email(self, email):
        if user_exists(email=email.data):
            raise ValidationError('That email is already registered. Please use a different one.')

# Add Teacher Form
class AddTeacherForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    full_name = StringField('Full Name', validators=[DataRequired()])
    phone = StringField('Phone Number')
    qualification = StringField('Qualification')
    submit = SubmitField('Add Teacher')
    
    def validate_username(self, username):
        if user_exists(username=username.data):
            raise ValidationError('That username is already taken. Please choose a different one.')
    
    def validate_email(self, email):
        if user_exists(email=email.data):
            raise ValidationError('That email is already registered. Please use a different one.')

# Teacher dashboard
@teacher.route('/dashboard')
@teacher_required
def dashboard():
    # Get teacher profile
    teacher = current_user.teacher_profile
    
    # Get counts for dashboard stats
    classes_count = Class.query.filter_by(teacher_id=teacher.id).count()
    subjects_count = Subject.query.filter_by(teacher_id=teacher.id).count()
    students_count = Student.query.join(Class).filter(Class.teacher_id==teacher.id).count()
    
    # Get upcoming exams
    upcoming_exams = Exam.query.filter_by(teacher_id=teacher.id, status='upcoming').order_by(Exam.exam_date).limit(5).all()
    
    # Get recent marks submissions
    recent_marks = Mark.query.join(Exam).filter(Exam.teacher_id==teacher.id).order_by(Mark.created_at.desc()).limit(10).all()
    
    # Get pending student mark submissions
    pending_marks = Mark.query.join(Exam).filter(
        Exam.teacher_id==teacher.id,
        Mark.status=='pending',
        Mark.submitted_by=='student'
    ).count()
    
    # Get recent questions from students
    recent_questions = Question.query.join(Subject).filter(
        Subject.teacher_id==teacher.id,
        Question.status=='open'
    ).order_by(Question.created_at.desc()).limit(5).all()
    
    return render_template('teacher/dashboard.html', 
                           title='Teacher Dashboard',
                           teacher=teacher,
                           classes_count=classes_count,
                           subjects_count=subjects_count,
                           students_count=students_count,
                           upcoming_exams=upcoming_exams,
                           recent_marks=recent_marks,
                           pending_marks=pending_marks,
                           recent_questions=recent_questions)

# Classes management
@teacher.route('/classes')
@teacher_required
def classes():
    # Get teacher profile
    teacher = current_user.teacher_profile
    
    # Get all classes taught by this teacher
    classes = Class.query.filter_by(teacher_id=teacher.id).all()
    
    return render_template('teacher/classes.html', title='My Classes', classes=classes)

# Class details
@teacher.route('/classes/<int:class_id>')
@teacher_required
def class_details(class_id):
    # Get teacher profile
    teacher = current_user.teacher_profile
    
    # Get class
    class_obj = Class.query.get_or_404(class_id)
    
    # Check if teacher has access to this class
    if class_obj.teacher_id != teacher.id:
        flash('You do not have permission to view this class.', 'danger')
        return redirect(url_for('teacher.classes'))
    
    # Get students in this class
    students = Student.query.filter_by(class_id=class_id).all()
    
    # Get subjects for this class
    subjects = Subject.query.filter_by(class_id=class_id, teacher_id=teacher.id).all()
    
    # Get exams for this class
    exams = Exam.query.filter_by(class_id=class_id, teacher_id=teacher.id).order_by(Exam.exam_date.desc()).all()
    
    return render_template('teacher/class_details.html', 
                           title=f'Class: {class_obj.name} - {class_obj.section}',
                           class_obj=class_obj,
                           students=students,
                           subjects=subjects,
                           exams=exams)

# Subjects management
@teacher.route('/subjects')
@teacher_required
def subjects():
    # Get teacher profile
    teacher = current_user.teacher_profile
    
    # Get all subjects taught by this teacher
    subjects = Subject.query.filter_by(teacher_id=teacher.id).all()
    
    return render_template('teacher/subjects.html', title='My Subjects', subjects=subjects)

# Subject details
@teacher.route('/subjects/<int:subject_id>')
@teacher_required
def subject_details(subject_id):
    # Get teacher profile
    teacher = current_user.teacher_profile
    
    # Get subject
    subject = Subject.query.get_or_404(subject_id)
    
    # Check if teacher has access to this subject
    if subject.teacher_id != teacher.id:
        flash('You do not have permission to view this subject.', 'danger')
        return redirect(url_for('teacher.subjects'))
    
    # Get exams for this subject
    exams = Exam.query.filter_by(subject_id=subject_id, teacher_id=teacher.id).order_by(Exam.exam_date.desc()).all()
    
    # Get notes for this subject
    notes = TeacherNote.query.filter_by(subject_id=subject_id, teacher_id=teacher.id).order_by(TeacherNote.created_at.desc()).all()
    
    # Get questions for this subject
    questions = Question.query.filter_by(subject_id=subject_id).order_by(Question.created_at.desc()).all()
    
    return render_template('teacher/subject_details.html', 
                           title=f'Subject: {subject.name}',
                           subject=subject,
                           exams=exams,
                           notes=notes,
                           questions=questions)

# Exam Form
class ExamForm(FlaskForm):
    title = StringField('Exam Title', validators=[DataRequired(), Length(min=2, max=100)])
    description = TextAreaField('Description')
    exam_type = SelectField('Exam Type', choices=[
        ('midterm', 'Midterm Exam'),
        ('final', 'Final Exam'),
        ('quiz', 'Quiz'),
        ('assignment', 'Assignment'),
        ('project', 'Project'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    subject = StringField('Subject', validators=[DataRequired(), Length(min=2, max=100)])
    class_name = StringField('Class', validators=[DataRequired(), Length(min=1, max=20)])
    total_marks = FloatField('Total Marks', validators=[DataRequired()])
    passing_marks = FloatField('Passing Marks', validators=[DataRequired()])
    exam_date = DateField('Exam Date', validators=[DataRequired()])
    status = SelectField('Status', choices=[
        ('upcoming', 'Upcoming'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed')
    ], validators=[DataRequired()])
    submit = SubmitField('Create Exam')

# Exams management
@teacher.route('/exams')
@teacher_required
def exams():
    # Get teacher profile
    teacher = current_user.teacher_profile
    
    # Get all exams created by this teacher
    exams = Exam.query.filter_by(teacher_id=teacher.id).order_by(Exam.exam_date.desc()).all()
    
    return render_template('teacher/exams.html', title='My Exams', exams=exams)

# Create new exam
@teacher.route('/exams/new', methods=['GET', 'POST'])
@teacher_required
def create_exam():
    # Get teacher profile
    teacher = current_user.teacher_profile
    
    form = ExamForm()
    
    if form.validate_on_submit():
        # Create a new exam with text input fields
        exam = Exam(
            title=form.title.data,
            description=form.description.data,
            exam_type=form.exam_type.data,
            class_id=None,  # We'll handle this differently
            subject_id=None,  # We'll handle this differently
            teacher_id=teacher.id,
            total_marks=form.total_marks.data,
            passing_marks=form.passing_marks.data,
            exam_date=form.exam_date.data,
            status=form.status.data
        )
        
        # Find or create a class based on the class_name input
        class_obj = Class.query.filter_by(name=form.class_name.data).first()
        if class_obj:
            exam.class_id = class_obj.id
        else:
            # If class doesn't exist, create a placeholder entry
            new_class = Class(
                name=form.class_name.data,
                section='A',  # Default section
                academic_year=datetime.datetime.now().year,
                teacher_id=teacher.id,
                school_id=teacher.school_id
            )
            db.session.add(new_class)
            db.session.flush()  # Get the ID without committing
            exam.class_id = new_class.id
        
        # Find or create a subject based on the subject input
        subject = Subject.query.filter_by(name=form.subject.data, class_id=exam.class_id).first()
        if subject:
            exam.subject_id = subject.id
        else:
            # If subject doesn't exist, create a placeholder entry
            new_subject = Subject(
                name=form.subject.data,
                code=form.subject.data[:5].upper(),  # Generate a simple code
                class_id=exam.class_id,
                teacher_id=teacher.id
            )
            db.session.add(new_subject)
            db.session.flush()  # Get the ID without committing
            exam.subject_id = new_subject.id
        
        db.session.add(exam)
        db.session.commit()
        
        flash(f'Exam "{form.title.data}" has been created successfully!', 'success')
        return redirect(url_for('teacher.exams'))
    
    return render_template('teacher/create_exam.html', title='Create New Exam', form=form)

# Edit exam
@teacher.route('/exams/<int:exam_id>/edit', methods=['GET', 'POST'])
@teacher_required
def edit_exam(exam_id):
    # Get teacher profile
    teacher = current_user.teacher_profile
    
    # Get exam
    exam = Exam.query.get_or_404(exam_id)
    
    # Check if teacher has access to this exam
    if exam.teacher_id != teacher.id:
        flash('You do not have permission to edit this exam.', 'danger')
        return redirect(url_for('teacher.exams'))
    
    form = ExamForm()
    
    if form.validate_on_submit():
        # Update basic exam details
        exam.title = form.title.data
        exam.description = form.description.data
        exam.exam_type = form.exam_type.data
        exam.total_marks = form.total_marks.data
        exam.passing_marks = form.passing_marks.data
        exam.exam_date = form.exam_date.data
        exam.status = form.status.data
        
        # Handle class_name field
        if form.class_name.data:
            # Find or create a class based on the class_name input
            class_obj = Class.query.filter_by(name=form.class_name.data).first()
            if class_obj:
                exam.class_id = class_obj.id
            else:
                # If class doesn't exist, create a placeholder entry
                new_class = Class(
                    name=form.class_name.data,
                    section='A',  # Default section
                    academic_year=datetime.datetime.now().year,
                    teacher_id=teacher.id,
                    school_id=teacher.school_id
                )
                db.session.add(new_class)
                db.session.flush()  # Get the ID without committing
                exam.class_id = new_class.id
        
        # Handle subject field
        if form.subject.data:
            # Find or create a subject based on the subject input
            subject = Subject.query.filter_by(name=form.subject.data, class_id=exam.class_id).first()
            if subject:
                exam.subject_id = subject.id
            else:
                # If subject doesn't exist, create a placeholder entry
                new_subject = Subject(
                    name=form.subject.data,
                    code=form.subject.data[:5].upper(),  # Generate a simple code
                    class_id=exam.class_id,
                    teacher_id=teacher.id
                )
                db.session.add(new_subject)
                db.session.flush()  # Get the ID without committing
                exam.subject_id = new_subject.id
        
        db.session.commit()
        
        flash(f'Exam "{exam.title}" has been updated successfully!', 'success')
        return redirect(url_for('teacher.exams'))
    
    # Pre-populate form fields
    if request.method == 'GET':
        form.title.data = exam.title
        form.description.data = exam.description
        form.exam_type.data = exam.exam_type
        
        # Get class and subject names from their IDs
        class_obj = Class.query.get(exam.class_id)
        if class_obj:
            form.class_name.data = class_obj.name
        
        subject = Subject.query.get(exam.subject_id)
        if subject:
            form.subject.data = subject.name
            
        form.total_marks.data = exam.total_marks
        form.passing_marks.data = exam.passing_marks
        form.exam_date.data = exam.exam_date
        form.status.data = exam.status
    
    return render_template('teacher/edit_exam.html', title='Edit Exam', form=form, exam=exam)

# Delete exam
@teacher.route('/exams/<int:exam_id>/delete', methods=['POST'])
@teacher_required
def delete_exam(exam_id):
    # Get teacher profile
    teacher = current_user.teacher_profile
    
    # Get exam
    exam = Exam.query.get_or_404(exam_id)
    
    # Check if teacher has access to this exam
    if exam.teacher_id != teacher.id:
        flash('You do not have permission to delete this exam.', 'danger')
        return redirect(url_for('teacher.exams'))
    
    db.session.delete(exam)
    db.session.commit()
    
    flash(f'Exam "{exam.title}" has been deleted successfully!', 'success')
    return redirect(url_for('teacher.exams'))

# View exam details
@teacher.route('/exams/<int:exam_id>', methods=['GET'])
@teacher_required
def view_exam(exam_id):
    # Get teacher profile
    teacher = current_user.teacher_profile
    
    # Get exam
    exam = Exam.query.get_or_404(exam_id)
    
    # Check if teacher has access to this exam
    if exam.teacher_id != teacher.id:
        flash('You do not have permission to view this exam.', 'danger')
        return redirect(url_for('teacher.exams'))
    
    # Get all marks for this exam
    marks = Mark.query.filter_by(exam_id=exam_id).all()
    
    # Get all students in this class
    students = Student.query.filter_by(class_id=exam.class_id).all()
    
    # Calculate statistics
    total_students = len(students)
    submitted_count = Mark.query.filter_by(exam_id=exam_id).count()
    pending_count = Mark.query.filter_by(exam_id=exam_id, status='pending').count()
    approved_count = Mark.query.filter_by(exam_id=exam_id, status='approved').count()
    
    # Calculate average marks
    avg_marks = 0
    if submitted_count > 0:
        avg_marks = sum(mark.marks_obtained for mark in marks) / submitted_count
    
    # Calculate pass percentage
    pass_count = sum(1 for mark in marks if mark.marks_obtained >= exam.passing_marks)
    pass_percentage = (pass_count / submitted_count * 100) if submitted_count > 0 else 0
    
    return render_template('teacher/view_exam.html', 
                           title=f'Exam: {exam.title}',
                           exam=exam,
                           marks=marks,
                           students=students,
                           total_students=total_students,
                           submitted_count=submitted_count,
                           pending_count=pending_count,
                           approved_count=approved_count,
                           avg_marks=avg_marks,
                           pass_percentage=pass_percentage)

# Mark Form
class MarkForm(FlaskForm):
    student_id = SelectField('Student', coerce=int, validators=[DataRequired()])
    marks_obtained = FloatField('Marks Obtained', validators=[DataRequired()])
    remarks = TextAreaField('Remarks')
    submit = SubmitField('Submit Marks')

# Add marks for a student
@teacher.route('/exams/<int:exam_id>/add-marks', methods=['GET', 'POST'])
@teacher_required
def add_marks(exam_id):
    # Get teacher profile
    teacher = current_user.teacher_profile
    
    # Get exam
    exam = Exam.query.get_or_404(exam_id)
    
    # Check if teacher has access to this exam
    if exam.teacher_id != teacher.id:
        flash('You do not have permission to add marks for this exam.', 'danger')
        return redirect(url_for('teacher.exams'))
    
    form = MarkForm()
    
    # Get all students in this class who don't have marks for this exam yet
    students_with_marks = [mark.student_id for mark in Mark.query.filter_by(exam_id=exam_id).all()]
    available_students = Student.query.filter_by(class_id=exam.class_id).filter(~Student.id.in_(students_with_marks)).all()
    
    # Populate form choices
    form.student_id.choices = [(s.id, f"{s.roll_number} - {s.full_name}") for s in available_students]
    
    if form.validate_on_submit():
        # Check if marks are within range
        if form.marks_obtained.data > exam.total_marks:
            flash(f'Marks obtained cannot be greater than total marks ({exam.total_marks}).', 'danger')
            return render_template('teacher/add_marks.html', title='Add Marks', form=form, exam=exam)
        
        mark = Mark(
            student_id=form.student_id.data,
            subject_id=exam.subject_id,
            exam_id=exam.id,
            marks_obtained=form.marks_obtained.data,
            remarks=form.remarks.data,
            submitted_by='teacher',
            status='approved'  # Teacher-submitted marks are automatically approved
        )
        
        db.session.add(mark)
        db.session.commit()
        
        flash('Marks have been added successfully!', 'success')
        return redirect(url_for('teacher.view_exam', exam_id=exam_id))
    
    return render_template('teacher/add_marks.html', title='Add Marks', form=form, exam=exam)

# Bulk add marks for an exam
@teacher.route('/exams/<int:exam_id>/bulk-add-marks', methods=['GET', 'POST'])
@teacher_required
def bulk_add_marks(exam_id):
    # Get teacher profile
    teacher = current_user.teacher_profile
    
    # Get exam
    exam = Exam.query.get_or_404(exam_id)
    
    # Check if teacher has access to this exam
    if exam.teacher_id != teacher.id:
        flash('You do not have permission to add marks for this exam.', 'danger')
        return redirect(url_for('teacher.exams'))
    
    # Get all students in this class
    students = Student.query.filter_by(class_id=exam.class_id).all()
    
    # Get existing marks
    existing_marks = {mark.student_id: mark for mark in Mark.query.filter_by(exam_id=exam_id).all()}
    
    if request.method == 'POST':
        # Process form submission
        for student in students:
            marks_key = f'marks_{student.id}'
            remarks_key = f'remarks_{student.id}'
            
            if marks_key in request.form and request.form[marks_key]:
                marks_obtained = float(request.form[marks_key])
                remarks = request.form.get(remarks_key, '')
                
                # Check if marks are within range
                if marks_obtained > exam.total_marks:
                    flash(f'Marks for {student.full_name} cannot be greater than total marks ({exam.total_marks}).', 'danger')
                    continue
                
                # Check if mark already exists
                if student.id in existing_marks:
                    # Update existing mark
                    mark = existing_marks[student.id]
                    mark.marks_obtained = marks_obtained
                    mark.remarks = remarks
                    mark.updated_at = datetime.utcnow()
                else:
                    # Create new mark
                    mark = Mark(
                        student_id=student.id,
                        subject_id=exam.subject_id,
                        exam_id=exam.id,
                        marks_obtained=marks_obtained,
                        remarks=remarks,
                        submitted_by='teacher',
                        status='approved'  # Teacher-submitted marks are automatically approved
                    )
                    db.session.add(mark)
        
        db.session.commit()
        flash('Marks have been saved successfully!', 'success')
        return redirect(url_for('teacher.view_exam', exam_id=exam_id))
    
    return render_template('teacher/bulk_add_marks.html', 
                           title='Bulk Add Marks',
                           exam=exam,
                           students=students,
                           existing_marks=existing_marks)

# Approve/Reject student submitted marks
@teacher.route('/marks/<int:mark_id>/update-status', methods=['POST'])
@teacher_required
def update_mark_status(mark_id):
    # Get teacher profile
    teacher = current_user.teacher_profile
    
    # Get mark
    mark = Mark.query.get_or_404(mark_id)
    
    # Check if teacher has access to this mark
    exam = Exam.query.get(mark.exam_id)
    if exam.teacher_id != teacher.id:
        flash('You do not have permission to update this mark.', 'danger')
        return redirect(url_for('teacher.exams'))
    
    status = request.form.get('status')
    if status not in ['approved', 'rejected']:
        flash('Invalid status.', 'danger')
        return redirect(url_for('teacher.view_exam', exam_id=mark.exam_id))
    
    mark.status = status
    db.session.commit()
    
    flash(f'Mark has been {status}.', 'success')
    return redirect(url_for('teacher.view_exam', exam_id=mark.exam_id))

# Teacher Note Form
class TeacherNoteForm(FlaskForm):
    subject_id = SelectField('Subject', coerce=int, validators=[DataRequired()])
    title = StringField('Title', validators=[DataRequired(), Length(min=2, max=100)])
    content = TextAreaField('Content', validators=[DataRequired()])
    submit = SubmitField('Save Note')

# Notes management
@teacher.route('/notes')
@teacher_required
def notes():
    # Get teacher profile
    teacher = current_user.teacher_profile
    
    # Get all notes created by this teacher
    notes = TeacherNote.query.filter_by(teacher_id=teacher.id).order_by(TeacherNote.created_at.desc()).all()
    
    return render_template('teacher/notes.html', title='My Notes', notes=notes)

# Create new note
@teacher.route('/notes/new', methods=['GET', 'POST'])
@teacher_required
def create_note():
    # Get teacher profile
    teacher = current_user.teacher_profile
    
    form = TeacherNoteForm()
    
    # Populate form choices
    form.subject_id.choices = [(s.id, s.name) for s in Subject.query.filter_by(teacher_id=teacher.id).all()]
    
    if form.validate_on_submit():
        note = TeacherNote(
            teacher_id=teacher.id,
            subject_id=form.subject_id.data,
            title=form.title.data,
            content=form.content.data
        )
        
        db.session.add(note)
        db.session.commit()
        
        flash(f'Note "{form.title.data}" has been created successfully!', 'success')
        return redirect(url_for('teacher.notes'))
    
    return render_template('teacher/create_note.html', title='Create New Note', form=form)

# Edit note
@teacher.route('/notes/<int:note_id>/edit', methods=['GET', 'POST'])
@teacher_required
def edit_note(note_id):
    # Get teacher profile
    teacher = current_user.teacher_profile
    
    # Get note
    note = TeacherNote.query.get_or_404(note_id)
    
    # Check if teacher has access to this note
    if note.teacher_id != teacher.id:
        flash('You do not have permission to edit this note.', 'danger')
        return redirect(url_for('teacher.notes'))
    
    form = TeacherNoteForm()
    
    # Populate form choices
    form.subject_id.choices = [(s.id, s.name) for s in Subject.query.filter_by(teacher_id=teacher.id).all()]
    
    if form.validate_on_submit():
        note.subject_id = form.subject_id.data
        note.title = form.title.data
        note.content = form.content.data
        
        db.session.commit()
        
        flash(f'Note "{note.title}" has been updated successfully!', 'success')
        return redirect(url_for('teacher.notes'))
    
    # Pre-populate form fields
    if request.method == 'GET':
        form.subject_id.data = note.subject_id
        form.title.data = note.title
        form.content.data = note.content
    
    return render_template('teacher/edit_note.html', title='Edit Note', form=form, note=note)

# Delete note
@teacher.route('/notes/<int:note_id>/delete', methods=['POST'])
@teacher_required
def delete_note(note_id):
    # Get teacher profile
    teacher = current_user.teacher_profile
    
    # Get note
    note = TeacherNote.query.get_or_404(note_id)
    
    # Check if teacher has access to this note
    if note.teacher_id != teacher.id:
        flash('You do not have permission to delete this note.', 'danger')
        return redirect(url_for('teacher.notes'))
    
    db.session.delete(note)
    db.session.commit()
    
    flash(f'Note "{note.title}" has been deleted successfully!', 'success')
    return redirect(url_for('teacher.notes'))

# Q&A management
@teacher.route('/questions')
@teacher_required
def questions():
    # Get teacher profile
    teacher = current_user.teacher_profile
    
    # Get all questions for subjects taught by this teacher
    questions = Question.query.join(Subject).filter(Subject.teacher_id==teacher.id).order_by(Question.created_at.desc()).all()
    
    return render_template('teacher/questions.html', title='Student Questions', questions=questions)

# View question details
@teacher.route('/questions/<int:question_id>', methods=['GET', 'POST'])
@teacher_required
def view_question(question_id):
    # Get teacher profile
    teacher = current_user.teacher_profile
    
    # Get question
    question = Question.query.get_or_404(question_id)
    
    # Check if teacher has access to this question
    if question.subject and question.subject.teacher_id != teacher.id:
        flash('You do not have permission to view this question.', 'danger')
        return redirect(url_for('teacher.questions'))
    
    # Get all answers for this question
    answers = Answer.query.filter_by(question_id=question_id).order_by(Answer.created_at).all()
    
    # Process form submission (new answer)
    if request.method == 'POST':
        content = request.form.get('content')
        
        if content:
            answer = Answer(
                question_id=question_id,
                user_id=current_user.id,
                content=content
            )
            
            db.session.add(answer)
            
            # Update question status
            question.status = 'answered'
            
            db.session.commit()
            
            flash('Your answer has been posted successfully!', 'success')
            return redirect(url_for('teacher.view_question', question_id=question_id))
    
    return render_template('teacher/view_question.html', 
                           title=f'Question: {question.title}',
                           question=question,
                           answers=answers)

# Routes
@teacher.route('/class_students/<int:class_id>')
@teacher_required
def class_students(class_id):
    # Get teacher profile
    teacher_profile = Teacher.query.filter_by(user_id=current_user.id).first()
    
    # Check if the teacher is assigned to this class
    class_obj = Class.query.filter_by(id=class_id, teacher_id=teacher_profile.id).first_or_404()
    
    # Get students in the class
    students = Student.query.filter_by(class_id=class_id).all()
    
    return render_template('teacher/class_students.html', 
                           title=f'Students in {class_obj.name} - {class_obj.section}', 
                           class_obj=class_obj, 
                           students=students)

@teacher.route('/class_rankings/<int:class_id>')
@teacher_required
def class_rankings(class_id):
    # Get teacher profile
    teacher_profile = Teacher.query.filter_by(user_id=current_user.id).first()
    
    # Check if the teacher is assigned to this class
    class_obj = Class.query.filter_by(id=class_id, teacher_id=teacher_profile.id).first_or_404()
    
    # Generate rankings
    rankings = generate_class_rankings(class_id)
    
    return render_template('teacher/class_rankings.html', 
                           title=f'Rankings for {class_obj.name} - {class_obj.section}', 
                           class_obj=class_obj, 
                           rankings=rankings)

@teacher.route('/subject_students/<int:subject_id>')
@teacher_required
def subject_students(subject_id):
    # Get teacher profile
    teacher_profile = Teacher.query.filter_by(user_id=current_user.id).first()
    
    # Check if the teacher is assigned to this subject
    subject = Subject.query.filter_by(id=subject_id, teacher_id=teacher_profile.id).first_or_404()
    
    # Get class
    class_obj = Class.query.get(subject.class_id)
    
    # Get students in the class
    students = Student.query.filter_by(class_id=class_obj.id).all()
    
    return render_template('teacher/subject_students.html', 
                           title=f'Students in {subject.name}', 
                           subject=subject, 
                           class_obj=class_obj, 
                           students=students)

# Mark management routes
@teacher.route('/marks')
@teacher_required
def marks():
    # Get teacher profile
    teacher_profile = Teacher.query.filter_by(user_id=current_user.id).first()
    
    # Get subjects taught by the teacher
    subjects = Subject.query.filter_by(teacher_id=teacher_profile.id).all()
    
    # Get marks for these subjects
    marks_data = []
    
    for subject in subjects:
        marks = Mark.query.filter_by(subject_id=subject.id).all()
        
        for mark in marks:
            student = Student.query.get(mark.student_id)
            exam = Exam.query.get(mark.exam_id)
            marks_data.append({
                'id': mark.id,
                'student_name': student.full_name,
                'subject_name': subject.name,
                'exam_type': exam.exam_type,
                'marks_obtained': mark.marks_obtained,
                'total_marks': exam.total_marks,
                'percentage': round(mark.marks_obtained / exam.total_marks * 100, 2),
                'date': mark.created_at.strftime('%d-%m-%Y')
            })
    
    return render_template('teacher/marks.html', title='Manage Marks', marks=marks_data)

@teacher.route('/add_mark', methods=['GET', 'POST'])
@teacher_required
def add_mark():
    # Get teacher profile
    teacher_profile = Teacher.query.filter_by(user_id=current_user.id).first()
    
    form = AddMarkForm()
    
    # Populate subject choices
    subjects = Subject.query.filter_by(teacher_id=teacher_profile.id).all()
    form.subject_id.choices = [(s.id, f"{s.name} ({s.code})") for s in subjects]
    
    # Populate student choices based on selected subject
    if request.method == 'GET' and request.args.get('subject_id'):
        subject_id = int(request.args.get('subject_id'))
        subject = Subject.query.get(subject_id)
        students = Student.query.filter_by(class_id=subject.class_id).all()
        form.student_id.choices = [(s.id, f"{s.full_name} ({s.roll_number})") for s in students]
    else:
        form.student_id.choices = []
    
    if form.validate_on_submit():
        mark = Mark(
            student_id=form.student_id.data,
            subject_id=form.subject_id.data,
            exam_id=form.exam_id.data,
            marks_obtained=form.marks_obtained.data,
            remarks=form.remarks.data,
            submitted_by='teacher',
            status='approved'  # Teacher-submitted marks are automatically approved
        )
        
        db.session.add(mark)
        db.session.commit()
        
        student = Student.query.get(form.student_id.data)
        subject = Subject.query.get(form.subject_id.data)
        
        flash(f'Mark added for {student.full_name} in {subject.name}!', 'success')
        return redirect(url_for('teacher.marks'))
    
    return render_template('teacher/add_mark.html', title='Add Mark', form=form)

@teacher.route('/edit_mark/<int:mark_id>', methods=['GET', 'POST'])
@teacher_required
def edit_mark(mark_id):
    # Get teacher profile
    teacher_profile = Teacher.query.filter_by(user_id=current_user.id).first()
    
    # Get mark
    mark = Mark.query.get_or_404(mark_id)
    
    # Check if the teacher is assigned to this subject
    subject = Subject.query.filter_by(id=mark.subject_id, teacher_id=teacher_profile.id).first_or_404()
    
    form = AddMarkForm()
    
    # Populate subject choices
    subjects = Subject.query.filter_by(teacher_id=teacher_profile.id).all()
    form.subject_id.choices = [(s.id, f"{s.name} ({s.code})") for s in subjects]
    
    # Populate student choices
    students = Student.query.filter_by(class_id=subject.class_id).all()
    form.student_id.choices = [(s.id, f"{s.full_name} ({s.roll_number})") for s in students]
    
    if form.validate_on_submit():
        mark.student_id = form.student_id.data
        mark.subject_id = form.subject_id.data
        mark.exam_id = form.exam_id.data
        mark.marks_obtained = form.marks_obtained.data
        mark.created_at = form.date.data
        
        db.session.commit()
        
        student = Student.query.get(form.student_id.data)
        subject = Subject.query.get(form.subject_id.data)
        
        flash(f'Mark updated for {student.full_name} in {subject.name}!', 'success')
        return redirect(url_for('teacher.marks'))
    
    # Populate form
    form.student_id.data = mark.student_id
    form.subject_id.data = mark.subject_id
    form.exam_id.data = mark.exam_id
    form.marks_obtained.data = mark.marks_obtained
    form.date.data = mark.created_at
    
    return render_template('teacher/edit_mark.html', title='Edit Mark', form=form, mark=mark)

@teacher.route('/delete_mark/<int:mark_id>', methods=['POST'])
@teacher_required
def delete_mark(mark_id):
    # Get teacher profile
    teacher_profile = Teacher.query.filter_by(user_id=current_user.id).first()
    
    # Get mark
    mark = Mark.query.get_or_404(mark_id)
    
    # Check if the teacher is assigned to this subject
    subject = Subject.query.filter_by(id=mark.subject_id, teacher_id=teacher_profile.id).first_or_404()
    
    db.session.delete(mark)
    db.session.commit()
    
    flash('Mark has been deleted!', 'success')
    return redirect(url_for('teacher.marks'))

# Attendance management routes
@teacher.route('/attendance')
@teacher_required
def attendance():
    # Get teacher profile
    teacher_profile = Teacher.query.filter_by(user_id=current_user.id).first()
    
    # Get classes taught by the teacher
    classes = Class.query.filter_by(teacher_id=teacher_profile.id).all()
    
    # Get attendance for students in these classes
    attendance_data = []
    
    for class_obj in classes:
        students = Student.query.filter_by(class_id=class_obj.id).all()
        
        for student in students:
            attendance_records = Attendance.query.filter_by(student_id=student.id).all()
            
            for record in attendance_records:
                attendance_data.append({
                    'id': record.id,
                    'student_name': student.full_name,
                    'class_name': f"{class_obj.name} - {class_obj.section}",
                    'date': record.date,
                    'status': record.status
                })
    
    return render_template('teacher/attendance.html', title='Manage Attendance', attendance=attendance_data)

@teacher.route('/add_attendance', methods=['GET', 'POST'])
@teacher_required
def add_attendance():
    # Get teacher profile
    teacher_profile = Teacher.query.filter_by(user_id=current_user.id).first()
    
    form = AddAttendanceForm()
    
    # Populate student choices
    students = []
    classes = Class.query.filter_by(teacher_id=teacher_profile.id).all()
    
    for class_obj in classes:
        class_students = Student.query.filter_by(class_id=class_obj.id).all()
        students.extend(class_students)
    
    form.student_id.choices = [(s.id, f"{s.full_name} ({Class.query.get(s.class_id).name} - {Class.query.get(s.class_id).section})") for s in students]
    
    if form.validate_on_submit():
        # Check if attendance already exists for this student on this date
        existing_attendance = Attendance.query.filter_by(
            student_id=form.student_id.data,
            date=form.date.data
        ).first()
        
        if existing_attendance:
            existing_attendance.status = form.status.data
            db.session.commit()
            flash('Attendance record updated!', 'success')
        else:
            attendance = Attendance(
                student_id=form.student_id.data,
                date=form.date.data,
                status=form.status.data
            )
            
            db.session.add(attendance)
            db.session.commit()
            
            student = Student.query.get(form.student_id.data)
            flash(f'Attendance added for {student.full_name}!', 'success')
        
        return redirect(url_for('teacher.attendance'))
    
    return render_template('teacher/add_attendance.html', title='Add Attendance', form=form)

@teacher.route('/edit_attendance/<int:attendance_id>', methods=['GET', 'POST'])
@teacher_required
def edit_attendance(attendance_id):
    # Get teacher profile
    teacher_profile = Teacher.query.filter_by(user_id=current_user.id).first()
    
    # Get attendance record
    attendance = Attendance.query.get_or_404(attendance_id)
    
    # Get student
    student = Student.query.get(attendance.student_id)
    
    # Check if the teacher is assigned to this student's class
    class_obj = Class.query.filter_by(id=student.class_id, teacher_id=teacher_profile.id).first_or_404()
    
    form = AddAttendanceForm()
    
    # Populate student choices
    students = []
    classes = Class.query.filter_by(teacher_id=teacher_profile.id).all()
    
    for class_obj in classes:
        class_students = Student.query.filter_by(class_id=class_obj.id).all()
        students.extend(class_students)
    
    form.student_id.choices = [(s.id, f"{s.full_name} ({Class.query.get(s.class_id).name} - {Class.query.get(s.class_id).section})") for s in students]
    
    if form.validate_on_submit():
        attendance.student_id = form.student_id.data
        attendance.date = form.date.data
        attendance.status = form.status.data
        
        db.session.commit()
        
        student = Student.query.get(form.student_id.data)
        flash(f'Attendance updated for {student.full_name}!', 'success')
        return redirect(url_for('teacher.attendance'))
    
    # Populate form
    form.student_id.data = attendance.student_id
    form.date.data = attendance.date
    form.status.data = attendance.status
    
    return render_template('teacher/edit_attendance.html', title='Edit Attendance', form=form, attendance=attendance)

@teacher.route('/delete_attendance/<int:attendance_id>', methods=['POST'])
@teacher_required
def delete_attendance(attendance_id):
    # Get teacher profile
    teacher_profile = Teacher.query.filter_by(user_id=current_user.id).first()
    
    # Get attendance record
    attendance = Attendance.query.get_or_404(attendance_id)
    
    # Get student
    student = Student.query.get(attendance.student_id)
    
    # Check if the teacher is assigned to this student's class
    class_obj = Class.query.filter_by(id=student.class_id, teacher_id=teacher_profile.id).first_or_404()
    
    db.session.delete(attendance)
    db.session.commit()
    
    flash('Attendance record has been deleted!', 'success')
    return redirect(url_for('teacher.attendance'))

# Student view routes
@teacher.route('/view_student/<int:student_id>')
@teacher_required
def view_student(student_id):
    # Get teacher profile
    teacher_profile = Teacher.query.filter_by(user_id=current_user.id).first()
    
    # Get student
    student = Student.query.get_or_404(student_id)
    
    # Check if the teacher is assigned to this student's class
    class_obj = Class.query.filter_by(id=student.class_id, teacher_id=teacher_profile.id).first_or_404()
    
    # Get performance data
    performance = generate_subject_performance(student_id)
    
    # Get attendance data
    attendance = Attendance.query.filter_by(student_id=student_id).all()
    
    return render_template('teacher/view_student.html', 
                           title=f'View Student: {student.full_name}', 
                           student=student, 
                           class_obj=class_obj, 
                           performance=performance, 
                           attendance=attendance)

@teacher.route('/add_student', methods=['GET', 'POST'])
@teacher_required
def add_student():
    # Get teacher profile
    teacher_profile = Teacher.query.filter_by(user_id=current_user.id).first()
    
    form = AddStudentForm()
    
    # Get all classes for the form dropdown
    form.class_id.choices = [(c.id, f"{c.name} - {c.section}") for c in Class.query.all()]
    
    if form.validate_on_submit():
        # Create user
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(
            username=form.username.data,
            email=form.email.data,
            password=hashed_password,
            role='student'
        )
        
        db.session.add(user)
        db.session.commit()
        
        # Create student profile
        student = Student(
            user_id=user.id,
            full_name=form.full_name.data,
            roll_number=form.roll_number.data,
            date_of_birth=form.date_of_birth.data,
            gender=form.gender.data,
            address=form.address.data,
            phone=form.phone.data,
            parent_name=form.parent_name.data,
            parent_phone=form.parent_phone.data,
            class_id=form.class_id.data
        )
        
        db.session.add(student)
        db.session.commit()
        
        flash(f'Student {form.full_name.data} has been added!', 'success')
        return redirect(url_for('teacher.dashboard'))
    
    return render_template('teacher/add_student.html', title='Add Student', form=form, teacher=teacher_profile)

@teacher.route('/add_teacher', methods=['GET', 'POST'])
@teacher_required
def add_teacher():
    # Get teacher profile
    teacher_profile = Teacher.query.filter_by(user_id=current_user.id).first()
    
    form = AddTeacherForm()
    
    if form.validate_on_submit():
        # Create user
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(
            username=form.username.data,
            email=form.email.data,
            password=hashed_password,
            role='teacher'
        )
        
        db.session.add(user)
        db.session.commit()
        
        # Create teacher profile
        new_teacher = Teacher(
            user_id=user.id,
            full_name=form.full_name.data,
            phone=form.phone.data,
            qualification=form.qualification.data
        )
        
        db.session.add(new_teacher)
        db.session.commit()
        
        flash(f'Teacher {form.full_name.data} has been added!', 'success')
        return redirect(url_for('teacher.dashboard'))
    
    return render_template('teacher/add_teacher.html', title='Add Teacher', form=form, teacher=teacher_profile) 