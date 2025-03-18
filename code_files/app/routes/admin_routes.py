from flask import Blueprint, render_template, redirect, url_for, flash, request, Response
from flask_login import login_required, current_user
from app import db, bcrypt
from app.models import User, Admin, Teacher, Student, Class, Subject, Mark, Attendance, School, Exam, Ranking, MasterAdmin
from app.utils import generate_class_rankings, generate_top_students, export_students_to_csv, user_exists, admin_required, master_admin_required
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, DateField, TextAreaField, FloatField, FileField
from wtforms.validators import DataRequired, Length, Email, ValidationError, EqualTo, NumberRange
import datetime

# Create blueprint
admin = Blueprint('admin', __name__)

# Forms
class AddTeacherForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    full_name = StringField('Full Name', validators=[DataRequired()])
    phone = StringField('Phone Number')
    qualification = StringField('Qualification')
    department = StringField('Department')
    experience = StringField('Years of Experience')
    category = SelectField('Teacher Category', choices=[
        ('PRT', 'Primary Teacher (PRT)'),
        ('TGT', 'Trained Graduate Teacher (TGT)'),
        ('PGT', 'Post Graduate Teacher (PGT)')
    ], validators=[DataRequired()])
    subject_specialization = StringField('Subject Specialization')
    school_id = SelectField('School', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Add Teacher')
    
    def validate_username(self, username):
        if user_exists(username=username.data):
            raise ValidationError('That username is already taken. Please choose a different one.')
    
    def validate_email(self, email):
        if user_exists(email=email.data):
            raise ValidationError('That email is already registered. Please use a different one.')

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
    school_id = SelectField('School', coerce=int, validators=[DataRequired()])
    class_id = SelectField('Class', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Add Student')
    
    def validate_username(self, username):
        if user_exists(username=username.data):
            raise ValidationError('That username is already taken. Please choose a different one.')
    
    def validate_email(self, email):
        if user_exists(email=email.data):
            raise ValidationError('That email is already registered. Please use a different one.')

class AddClassForm(FlaskForm):
    name = StringField('Class Name', validators=[DataRequired()])
    section = SelectField('Section', choices=[
        ('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D'), ('E', 'E')
    ], validators=[DataRequired()])
    stream = SelectField('Stream (Only for Classes 11-12)', choices=[
        ('', 'None'),
        ('Science', 'Science'),
        ('Commerce', 'Commerce'),
        ('Arts', 'Arts')
    ])
    academic_year = StringField('Academic Year', validators=[DataRequired()])
    teacher_id = SelectField('Class Teacher', coerce=int, validators=[DataRequired()])
    school_id = SelectField('School', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Add Class')

    def validate(self):
        if not super().validate():
            return False
        
        # Check if stream is selected for classes 11-12 and not selected for other classes
        try:
            class_number = int(self.name.data)
            if class_number in [11, 12]:
                if not self.stream.data:
                    self.stream.errors = ["Stream is required for Classes 11 and 12"]
                    return False
            else:
                if self.stream.data:
                    self.stream.errors = ["Stream should only be selected for Classes 11 and 12"]
                    return False
        except ValueError:
            self.name.errors = ["Class name should be a number from 1 to 12"]
            return False
        
        return True

class AddSubjectForm(FlaskForm):
    name = StringField('Subject Name', validators=[DataRequired()])
    code = StringField('Subject Code', validators=[DataRequired()])
    description = TextAreaField('Description')
    class_id = SelectField('Class', coerce=int, validators=[DataRequired()])
    teacher_id = SelectField('Teacher', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Add Subject')

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
    school = StringField('School', validators=[DataRequired(), Length(min=2, max=100)])
    class_name = StringField('Class', validators=[DataRequired(), Length(min=1, max=20)])
    teacher_id = SelectField('Teacher', coerce=int, validators=[DataRequired()])
    total_marks = FloatField('Total Marks', validators=[DataRequired()])
    passing_marks = FloatField('Passing Marks', validators=[DataRequired()])
    exam_date = DateField('Exam Date', validators=[DataRequired()])
    status = SelectField('Status', choices=[
        ('upcoming', 'Upcoming'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed')
    ], validators=[DataRequired()])
    submit = SubmitField('Create Exam')

class SettingsForm(FlaskForm):
    school_name = StringField('School Name', validators=[DataRequired(), Length(max=100)])
    academic_year = StringField('Academic Year', validators=[DataRequired(), Length(max=20)])
    term = SelectField('Term', choices=[('1', 'Term 1'), ('2', 'Term 2'), ('3', 'Term 3')], validators=[DataRequired()])
    passing_percentage = FloatField('Passing Percentage', validators=[DataRequired(), NumberRange(min=0, max=100)])
    submit = SubmitField('Save Changes')

class AccountUpdateForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[EqualTo('new_password')])
    submit = SubmitField('Update Account')

class RestoreForm(FlaskForm):
    backup_file = FileField('Backup File', validators=[DataRequired()])
    submit = SubmitField('Restore Backup')

# Routes
@admin.route('/dashboard')
@admin_required
def dashboard():
    # Get counts for dashboard
    student_count = Student.query.count()
    teacher_count = Teacher.query.count()
    class_count = Class.query.count()
    subject_count = Subject.query.count()
    
    # Get top students
    top_students = generate_top_students(limit=5)
    
    return render_template('admin/dashboard.html', 
                           title='Admin Dashboard',
                           student_count=student_count,
                           teacher_count=teacher_count,
                           class_count=class_count,
                           subject_count=subject_count,
                           top_students=top_students)

# Teacher management routes
@admin.route('/teachers')
@admin_required
def teachers():
    # Get filter parameters
    school_id = request.args.get('school_id', type=int)
    
    # Query teachers with optional school filter
    if school_id:
        teachers = Teacher.query.filter_by(school_id=school_id).all()
    else:
        teachers = Teacher.query.all()
    
    # Get all schools for filtering
    schools = School.query.all()
    
    return render_template('admin/teachers.html', 
                          title='Manage Teachers', 
                          teachers=teachers,
                          schools=schools,
                          current_school_id=school_id)

@admin.route('/add_teacher', methods=['GET', 'POST'])
@admin_required
def add_teacher():
    form = AddTeacherForm()
    
    # Populate school choices
    form.school_id.choices = [(s.id, s.name) for s in School.query.all()]
    
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
        teacher = Teacher(
            user_id=user.id,
            full_name=form.full_name.data,
            phone=form.phone.data,
            qualification=form.qualification.data,
            department=form.department.data,
            experience=form.experience.data,
            category=form.category.data,
            subject_specialization=form.subject_specialization.data,
            school_id=form.school_id.data
        )
        
        db.session.add(teacher)
        db.session.commit()
        
        flash(f'Teacher account created for {form.full_name.data}!', 'success')
        return redirect(url_for('admin.teachers'))
    
    return render_template('admin/add_teacher.html', title='Add Teacher', form=form)

@admin.route('/view_teacher/<int:teacher_id>')
@admin_required
def view_teacher(teacher_id):
    teacher = Teacher.query.get_or_404(teacher_id)
    user = User.query.get(teacher.user_id)
    school = School.query.get(teacher.school_id) if teacher.school_id else None
    classes = Class.query.filter_by(teacher_id=teacher.id).all()
    subjects = Subject.query.filter_by(teacher_id=teacher.id).all()
    
    return render_template('admin/view_teacher.html', 
                          title=f'View Teacher: {teacher.full_name}', 
                          teacher=teacher,
                          user=user,
                          school=school,
                          classes=classes,
                          subjects=subjects)

@admin.route('/edit_teacher/<int:teacher_id>', methods=['GET', 'POST'])
@admin_required
def edit_teacher(teacher_id):
    teacher = Teacher.query.get_or_404(teacher_id)
    user = User.query.get(teacher.user_id)
    
    form = AddTeacherForm()
    
    # Populate school choices
    form.school_id.choices = [(s.id, s.name) for s in School.query.all()]
    
    if form.validate_on_submit():
        # Update user
        if user.username != form.username.data and user_exists(username=form.username.data):
            flash('That username is already taken. Please choose a different one.', 'danger')
        elif user.email != form.email.data and user_exists(email=form.email.data):
            flash('That email is already registered. Please use a different one.', 'danger')
        else:
            user.username = form.username.data
            user.email = form.email.data
            
            if form.password.data:
                user.password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
            
            # Update teacher profile
            teacher.full_name = form.full_name.data
            teacher.phone = form.phone.data
            teacher.qualification = form.qualification.data
            teacher.department = form.department.data
            teacher.experience = form.experience.data
            teacher.category = form.category.data
            teacher.subject_specialization = form.subject_specialization.data
            teacher.school_id = form.school_id.data
            
            db.session.commit()
            
            flash(f'Teacher account updated for {form.full_name.data}!', 'success')
            return redirect(url_for('admin.teachers'))
    
    # Populate form
    form.username.data = user.username
    form.email.data = user.email
    form.full_name.data = teacher.full_name
    form.phone.data = teacher.phone
    form.qualification.data = teacher.qualification
    form.department.data = teacher.department if teacher.department else ""
    form.experience.data = teacher.experience if teacher.experience else ""
    form.category.data = teacher.category if teacher.category else "TGT"
    form.subject_specialization.data = teacher.subject_specialization if teacher.subject_specialization else ""
    if teacher.school_id:
        form.school_id.data = teacher.school_id
    
    return render_template('admin/edit_teacher.html', title='Edit Teacher', form=form, teacher=teacher)

@admin.route('/delete_teacher/<int:teacher_id>', methods=['POST'])
@admin_required
def delete_teacher(teacher_id):
    teacher = Teacher.query.get_or_404(teacher_id)
    user = User.query.get(teacher.user_id)
    
    db.session.delete(teacher)
    db.session.delete(user)
    db.session.commit()
    
    flash('Teacher has been deleted!', 'success')
    return redirect(url_for('admin.teachers'))

# Student management routes
@admin.route('/students')
@admin_required
def students():
    # Get filter parameters
    school_id = request.args.get('school_id', type=int)
    
    # Query students with optional school filter
    if school_id:
        students = Student.query.filter_by(school_id=school_id).all()
    else:
        students = Student.query.all()
    
    # Get all classes and schools for filtering
    classes = Class.query.all()
    schools = School.query.all()
    
    return render_template('admin/students.html', 
                          title='Manage Students', 
                          students=students, 
                          classes=classes,
                          schools=schools,
                          current_school_id=school_id)

@admin.route('/add_student', methods=['GET', 'POST'])
@admin_required
def add_student():
    form = AddStudentForm()
    
    # Populate school choices
    form.school_id.choices = [(s.id, s.name) for s in School.query.all()]
    
    # Populate class choices
    selected_school_id = request.args.get('school_id', type=int)
    if selected_school_id:
        form.class_id.choices = [(c.id, f"{c.name} - {c.section}") for c in Class.query.filter_by(school_id=selected_school_id).all()]
    else:
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
            class_id=form.class_id.data,
            school_id=form.school_id.data
        )
        
        db.session.add(student)
        db.session.commit()
        
        flash(f'Student account created for {form.full_name.data}!', 'success')
        return redirect(url_for('admin.students'))
    
    return render_template('admin/add_student.html', title='Add Student', form=form)

@admin.route('/edit_student/<int:student_id>', methods=['GET', 'POST'])
@admin_required
def edit_student(student_id):
    student = Student.query.get_or_404(student_id)
    user = User.query.get(student.user_id)
    
    form = AddStudentForm()
    
    # Populate school choices
    form.school_id.choices = [(s.id, s.name) for s in School.query.all()]
    
    # Populate class choices based on selected school
    selected_school_id = request.args.get('school_id', type=int) or student.school_id
    if selected_school_id:
        form.class_id.choices = [(c.id, f"{c.name} - {c.section}") for c in Class.query.filter_by(school_id=selected_school_id).all()]
    else:
        form.class_id.choices = [(c.id, f"{c.name} - {c.section}") for c in Class.query.all()]
    
    if form.validate_on_submit():
        # Update user
        if user.username != form.username.data and user_exists(username=form.username.data):
            flash('That username is already taken. Please choose a different one.', 'danger')
        elif user.email != form.email.data and user_exists(email=form.email.data):
            flash('That email is already registered. Please use a different one.', 'danger')
        else:
            user.username = form.username.data
            user.email = form.email.data
            
            if form.password.data:
                user.password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
            
            # Update student profile
            student.full_name = form.full_name.data
            student.roll_number = form.roll_number.data
            student.date_of_birth = form.date_of_birth.data
            student.gender = form.gender.data
            student.address = form.address.data
            student.phone = form.phone.data
            student.parent_name = form.parent_name.data
            student.parent_phone = form.parent_phone.data
            student.class_id = form.class_id.data
            student.school_id = form.school_id.data
            
            db.session.commit()
            
            flash(f'Student account updated for {form.full_name.data}!', 'success')
            return redirect(url_for('admin.students'))
    
    # Populate form
    form.username.data = user.username
    form.email.data = user.email
    form.full_name.data = student.full_name
    form.roll_number.data = student.roll_number
    form.date_of_birth.data = student.date_of_birth
    form.gender.data = student.gender
    form.address.data = student.address
    form.phone.data = student.phone
    form.parent_name.data = student.parent_name
    form.parent_phone.data = student.parent_phone
    form.class_id.data = student.class_id
    if student.school_id:
        form.school_id.data = student.school_id
    
    return render_template('admin/edit_student.html', title='Edit Student', form=form, student=student)

@admin.route('/delete_student/<int:student_id>', methods=['POST'])
@admin_required
def delete_student(student_id):
    student = Student.query.get_or_404(student_id)
    user = User.query.get(student.user_id)
    
    db.session.delete(student)
    db.session.delete(user)
    db.session.commit()
    
    flash('Student has been deleted!', 'success')
    return redirect(url_for('admin.students'))

@admin.route('/view_student/<int:student_id>')
@admin_required
def view_student(student_id):
    student = Student.query.get_or_404(student_id)
    user = User.query.get(student.user_id)
    class_obj = Class.query.get(student.class_id)
    school = School.query.get(student.school_id) if student.school_id else None
    teacher = Teacher.query.get(class_obj.teacher_id) if class_obj else None
    
    # Get performance data
    marks = Mark.query.filter_by(student_id=student_id).all()
    total_marks = sum([mark.marks_obtained for mark in marks]) if marks else 0
    total_possible = sum([mark.total_marks for mark in marks]) if marks else 0
    average_percentage = (total_marks / total_possible * 100) if total_possible > 0 else 0
    
    # Get attendance data
    attendance = Attendance.query.filter_by(student_id=student_id).all()
    present_count = sum([1 for a in attendance if a.status == 'present']) if attendance else 0
    absent_count = sum([1 for a in attendance if a.status == 'absent']) if attendance else 0
    late_count = sum([1 for a in attendance if a.status == 'late']) if attendance else 0
    total_days = len(attendance) if attendance else 0
    attendance_percentage = (present_count / total_days * 100) if total_days > 0 else 0
    
    return render_template('admin/view_student.html', 
                          title=f'View Student: {student.full_name}', 
                          student=student,
                          user=user,
                          class_obj=class_obj,
                          school=school,
                          teacher=teacher,
                          marks=marks,
                          average_percentage=average_percentage,
                          attendance=attendance,
                          present_count=present_count,
                          absent_count=absent_count,
                          late_count=late_count,
                          attendance_percentage=attendance_percentage)

# Class management routes
@admin.route('/classes')
@admin_required
def classes():
    # Get filter parameters
    school_id = request.args.get('school_id', type=int)
    
    # Query classes with optional school filter
    if school_id:
        classes = Class.query.filter_by(school_id=school_id).all()
    else:
        classes = Class.query.all()
    
    # Get all schools for filtering
    schools = School.query.all()
    
    return render_template('admin/classes.html', 
                          title='Manage Classes', 
                          classes=classes,
                          schools=schools,
                          current_school_id=school_id)

@admin.route('/add_class', methods=['GET', 'POST'])
@admin_required
def add_class():
    form = AddClassForm()
    
    # Populate school choices
    form.school_id.choices = [(s.id, s.name) for s in School.query.all()]
    
    # Get class name from form if submitted
    class_name = request.form.get('name', '')
    try:
        class_number = int(class_name) if class_name else 0
    except ValueError:
        class_number = 0
    
    # Determine teacher category based on class number
    teacher_category = None
    if 1 <= class_number <= 5:
        teacher_category = 'PRT'
    elif 6 <= class_number <= 10:
        teacher_category = 'TGT'
    elif 11 <= class_number <= 12:
        teacher_category = 'PGT'
    
    # Populate teacher choices based on selected school and appropriate category
    selected_school_id = request.args.get('school_id', type=int)
    if selected_school_id:
        if teacher_category:
            form.teacher_id.choices = [(t.id, f"{t.full_name} ({t.category})") 
                                      for t in Teacher.query.filter_by(school_id=selected_school_id, category=teacher_category).all()]
        else:
            form.teacher_id.choices = [(t.id, f"{t.full_name} ({t.category})") 
                                      for t in Teacher.query.filter_by(school_id=selected_school_id).all()]
    else:
        if teacher_category:
            form.teacher_id.choices = [(t.id, f"{t.full_name} ({t.category})") 
                                      for t in Teacher.query.filter_by(category=teacher_category).all()]
        else:
            form.teacher_id.choices = [(t.id, f"{t.full_name} ({t.category})") 
                                      for t in Teacher.query.all()]
    
    if form.validate_on_submit():
        # Validate teacher category matches class level
        teacher = Teacher.query.get(form.teacher_id.data)
        class_number = int(form.name.data)
        
        if 1 <= class_number <= 5 and teacher.category != 'PRT':
            flash(f'Classes 1-5 must be assigned a Primary Teacher (PRT)', 'danger')
        elif 6 <= class_number <= 10 and teacher.category != 'TGT':
            flash(f'Classes 6-10 must be assigned a Trained Graduate Teacher (TGT)', 'danger')
        elif 11 <= class_number <= 12 and teacher.category != 'PGT':
            flash(f'Classes 11-12 must be assigned a Post Graduate Teacher (PGT)', 'danger')
        else:
            class_obj = Class(
                name=form.name.data,
                section=form.section.data,
                stream=form.stream.data if class_number in [11, 12] else None,
                academic_year=form.academic_year.data,
                teacher_id=form.teacher_id.data,
                school_id=form.school_id.data
            )
            
            db.session.add(class_obj)
            db.session.commit()
            
            flash(f'Class {form.name.data} - {form.section.data} has been created!', 'success')
            return redirect(url_for('admin.classes'))
    
    return render_template('admin/add_class.html', title='Add Class', form=form)

@admin.route('/edit_class/<int:class_id>', methods=['GET', 'POST'])
@admin_required
def edit_class(class_id):
    class_obj = Class.query.get_or_404(class_id)
    
    form = AddClassForm()
    
    # Populate school choices
    form.school_id.choices = [(s.id, s.name) for s in School.query.all()]
    
    # Get class name from form if submitted, otherwise use existing class name
    class_name = request.form.get('name', class_obj.name)
    try:
        class_number = int(class_name)
    except ValueError:
        class_number = 0
    
    # Determine teacher category based on class number
    teacher_category = None
    if 1 <= class_number <= 5:
        teacher_category = 'PRT'
    elif 6 <= class_number <= 10:
        teacher_category = 'TGT'
    elif 11 <= class_number <= 12:
        teacher_category = 'PGT'
    
    # Populate teacher choices based on selected school and appropriate category
    selected_school_id = request.args.get('school_id', type=int) or class_obj.school_id
    if selected_school_id:
        if teacher_category:
            form.teacher_id.choices = [(t.id, f"{t.full_name} ({t.category})") 
                                      for t in Teacher.query.filter_by(school_id=selected_school_id, category=teacher_category).all()]
            # Add current teacher if not in the filtered list
            current_teacher = Teacher.query.get(class_obj.teacher_id)
            if current_teacher and current_teacher.id not in [t[0] for t in form.teacher_id.choices]:
                form.teacher_id.choices.append((current_teacher.id, f"{current_teacher.full_name} ({current_teacher.category}) - Current"))
        else:
            form.teacher_id.choices = [(t.id, f"{t.full_name} ({t.category})") 
                                      for t in Teacher.query.filter_by(school_id=selected_school_id).all()]
    else:
        if teacher_category:
            form.teacher_id.choices = [(t.id, f"{t.full_name} ({t.category})") 
                                      for t in Teacher.query.filter_by(category=teacher_category).all()]
            # Add current teacher if not in the filtered list
            current_teacher = Teacher.query.get(class_obj.teacher_id)
            if current_teacher and current_teacher.id not in [t[0] for t in form.teacher_id.choices]:
                form.teacher_id.choices.append((current_teacher.id, f"{current_teacher.full_name} ({current_teacher.category}) - Current"))
        else:
            form.teacher_id.choices = [(t.id, f"{t.full_name} ({t.category})") 
                                      for t in Teacher.query.all()]
    
    if form.validate_on_submit():
        # Validate teacher category matches class level
        teacher = Teacher.query.get(form.teacher_id.data)
        class_number = int(form.name.data)
        
        if 1 <= class_number <= 5 and teacher.category != 'PRT':
            flash(f'Classes 1-5 must be assigned a Primary Teacher (PRT)', 'danger')
        elif 6 <= class_number <= 10 and teacher.category != 'TGT':
            flash(f'Classes 6-10 must be assigned a Trained Graduate Teacher (TGT)', 'danger')
        elif 11 <= class_number <= 12 and teacher.category != 'PGT':
            flash(f'Classes 11-12 must be assigned a Post Graduate Teacher (PGT)', 'danger')
        else:
            class_obj.name = form.name.data
            class_obj.section = form.section.data
            class_obj.stream = form.stream.data if class_number in [11, 12] else None
            class_obj.academic_year = form.academic_year.data
            class_obj.teacher_id = form.teacher_id.data
            class_obj.school_id = form.school_id.data
            
            db.session.commit()
            
            flash(f'Class {form.name.data} - {form.section.data} has been updated!', 'success')
            return redirect(url_for('admin.classes'))
    
    # Populate form
    form.name.data = class_obj.name
    form.section.data = class_obj.section
    form.stream.data = class_obj.stream if class_obj.stream else ""
    form.academic_year.data = class_obj.academic_year
    form.teacher_id.data = class_obj.teacher_id
    if class_obj.school_id:
        form.school_id.data = class_obj.school_id
    
    return render_template('admin/edit_class.html', title='Edit Class', form=form, class_obj=class_obj)

@admin.route('/delete_class/<int:class_id>', methods=['POST'])
@admin_required
def delete_class(class_id):
    class_obj = Class.query.get_or_404(class_id)
    
    # Check if there are any students in this class
    students_count = Student.query.filter_by(class_id=class_id).count()
    if students_count > 0:
        flash(f'Cannot delete class {class_obj.name} - {class_obj.section} because there are {students_count} students assigned to it. Please reassign or delete these students first.', 'danger')
        return redirect(url_for('admin.classes'))
    
    # Check if there are any subjects for this class
    subjects_count = Subject.query.filter_by(class_id=class_id).count()
    if subjects_count > 0:
        flash(f'Cannot delete class {class_obj.name} - {class_obj.section} because there are {subjects_count} subjects assigned to it. Please delete these subjects first.', 'danger')
        return redirect(url_for('admin.classes'))
    
    # Check if there are any exams for this class
    exams_count = Exam.query.filter_by(class_id=class_id).count()
    if exams_count > 0:
        flash(f'Cannot delete class {class_obj.name} - {class_obj.section} because there are {exams_count} exams assigned to it. Please delete these exams first.', 'danger')
        return redirect(url_for('admin.classes'))
    
    # If no dependencies, proceed with deletion
    db.session.delete(class_obj)
    db.session.commit()
    
    flash('Class has been deleted!', 'success')
    return redirect(url_for('admin.classes'))

@admin.route('/class_students/<int:class_id>')
@admin_required
def class_students(class_id):
    class_obj = Class.query.get_or_404(class_id)
    students = Student.query.filter_by(class_id=class_id).all()
    
    return render_template('admin/class_students.html', title=f'Students in {class_obj.name} - {class_obj.section}', class_obj=class_obj, students=students)

# Subject management routes
@admin.route('/subjects')
@admin_required
def subjects():
    # Get filter parameters
    school_id = request.args.get('school_id', type=int)
    
    # Query subjects with optional school filter
    if school_id:
        subjects = Subject.query.join(Class).filter(Class.school_id == school_id).all()
    else:
        subjects = Subject.query.all()
    
    # Get all schools for filtering
    schools = School.query.all()
    
    return render_template('admin/subjects.html', 
                          title='Manage Subjects', 
                          subjects=subjects,
                          schools=schools,
                          current_school_id=school_id)

@admin.route('/add_subject', methods=['GET', 'POST'])
@admin_required
def add_subject():
    form = AddSubjectForm()
    
    # Populate class choices
    form.class_id.choices = [(c.id, f"{c.name} - {c.section}") for c in Class.query.all()]
    
    # Get selected class to filter teachers
    selected_class_id = request.form.get('class_id', type=int)
    if selected_class_id:
        selected_class = Class.query.get(selected_class_id)
        if selected_class:
            try:
                class_number = int(selected_class.name)
                # Filter teachers based on class level
                if 1 <= class_number <= 5:
                    form.teacher_id.choices = [(t.id, f"{t.full_name} ({t.category})") 
                                             for t in Teacher.query.filter_by(category='PRT').all()]
                elif 6 <= class_number <= 10:
                    form.teacher_id.choices = [(t.id, f"{t.full_name} ({t.category})") 
                                             for t in Teacher.query.filter_by(category='TGT').all()]
                elif 11 <= class_number <= 12:
                    form.teacher_id.choices = [(t.id, f"{t.full_name} ({t.category})") 
                                             for t in Teacher.query.filter_by(category='PGT').all()]
                else:
                    form.teacher_id.choices = [(t.id, f"{t.full_name} ({t.category})") for t in Teacher.query.all()]
            except ValueError:
                form.teacher_id.choices = [(t.id, f"{t.full_name} ({t.category})") for t in Teacher.query.all()]
        else:
            form.teacher_id.choices = [(t.id, f"{t.full_name} ({t.category})") for t in Teacher.query.all()]
    else:
        form.teacher_id.choices = [(t.id, f"{t.full_name} ({t.category})") for t in Teacher.query.all()]
    
    if form.validate_on_submit():
        # Validate teacher category matches class level
        teacher = Teacher.query.get(form.teacher_id.data)
        selected_class = Class.query.get(form.class_id.data)
        
        try:
            class_number = int(selected_class.name)
            valid_assignment = True
            
            if 1 <= class_number <= 5 and teacher.category != 'PRT':
                flash(f'Classes 1-5 must be assigned a Primary Teacher (PRT)', 'danger')
                valid_assignment = False
            elif 6 <= class_number <= 10 and teacher.category != 'TGT':
                flash(f'Classes 6-10 must be assigned a Trained Graduate Teacher (TGT)', 'danger')
                valid_assignment = False
            elif 11 <= class_number <= 12 and teacher.category != 'PGT':
                flash(f'Classes 11-12 must be assigned a Post Graduate Teacher (PGT)', 'danger')
                valid_assignment = False
            
            if not valid_assignment:
                return render_template('admin/add_subject.html', title='Add Subject', form=form)
                
        except ValueError:
            # If class name is not a number, skip validation
            pass
        
        subject = Subject(
            name=form.name.data,
            code=form.code.data,
            description=form.description.data,
            class_id=form.class_id.data,
            teacher_id=form.teacher_id.data
        )
        
        db.session.add(subject)
        db.session.commit()
        
        flash(f'Subject {form.name.data} has been created!', 'success')
        return redirect(url_for('admin.subjects'))
    
    return render_template('admin/add_subject.html', title='Add Subject', form=form)

@admin.route('/edit_subject/<int:subject_id>', methods=['GET', 'POST'])
@admin_required
def edit_subject(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    
    form = AddSubjectForm()
    
    # Populate class choices
    form.class_id.choices = [(c.id, f"{c.name} - {c.section}") for c in Class.query.all()]
    
    # Get selected class to filter teachers
    selected_class_id = request.form.get('class_id', type=int) or subject.class_id
    if selected_class_id:
        selected_class = Class.query.get(selected_class_id)
        if selected_class:
            try:
                class_number = int(selected_class.name)
                # Filter teachers based on class level
                if 1 <= class_number <= 5:
                    form.teacher_id.choices = [(t.id, f"{t.full_name} ({t.category})") 
                                             for t in Teacher.query.filter_by(category='PRT').all()]
                elif 6 <= class_number <= 10:
                    form.teacher_id.choices = [(t.id, f"{t.full_name} ({t.category})") 
                                             for t in Teacher.query.filter_by(category='TGT').all()]
                elif 11 <= class_number <= 12:
                    form.teacher_id.choices = [(t.id, f"{t.full_name} ({t.category})") 
                                             for t in Teacher.query.filter_by(category='PGT').all()]
                else:
                    form.teacher_id.choices = [(t.id, f"{t.full_name} ({t.category})") for t in Teacher.query.all()]
                
                # Add current teacher if not in the filtered list
                current_teacher = Teacher.query.get(subject.teacher_id)
                if current_teacher and current_teacher.id not in [t[0] for t in form.teacher_id.choices]:
                    form.teacher_id.choices.append((current_teacher.id, f"{current_teacher.full_name} ({current_teacher.category}) - Current"))
            except ValueError:
                form.teacher_id.choices = [(t.id, f"{t.full_name} ({t.category})") for t in Teacher.query.all()]
        else:
            form.teacher_id.choices = [(t.id, f"{t.full_name} ({t.category})") for t in Teacher.query.all()]
    else:
        form.teacher_id.choices = [(t.id, f"{t.full_name} ({t.category})") for t in Teacher.query.all()]
    
    if form.validate_on_submit():
        # Validate teacher category matches class level
        teacher = Teacher.query.get(form.teacher_id.data)
        selected_class = Class.query.get(form.class_id.data)
        
        try:
            class_number = int(selected_class.name)
            valid_assignment = True
            
            if 1 <= class_number <= 5 and teacher.category != 'PRT':
                flash(f'Classes 1-5 must be assigned a Primary Teacher (PRT)', 'danger')
                valid_assignment = False
            elif 6 <= class_number <= 10 and teacher.category != 'TGT':
                flash(f'Classes 6-10 must be assigned a Trained Graduate Teacher (TGT)', 'danger')
                valid_assignment = False
            elif 11 <= class_number <= 12 and teacher.category != 'PGT':
                flash(f'Classes 11-12 must be assigned a Post Graduate Teacher (PGT)', 'danger')
                valid_assignment = False
            
            if not valid_assignment:
                return render_template('admin/edit_subject.html', title='Edit Subject', form=form, subject=subject)
                
        except ValueError:
            # If class name is not a number, skip validation
            pass
        
        subject.name = form.name.data
        subject.code = form.code.data
        subject.description = form.description.data
        subject.class_id = form.class_id.data
        subject.teacher_id = form.teacher_id.data
        
        db.session.commit()
        
        flash(f'Subject {form.name.data} has been updated!', 'success')
        return redirect(url_for('admin.subjects'))
    
    # Populate form
    form.name.data = subject.name
    form.code.data = subject.code
    form.description.data = subject.description
    form.class_id.data = subject.class_id
    form.teacher_id.data = subject.teacher_id
    
    return render_template('admin/edit_subject.html', title='Edit Subject', form=form, subject=subject)

@admin.route('/delete_subject/<int:subject_id>', methods=['POST'])
@admin_required
def delete_subject(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    
    db.session.delete(subject)
    db.session.commit()
    
    flash('Subject has been deleted!', 'success')
    return redirect(url_for('admin.subjects'))

# Analytics routes
@admin.route('/class_rankings/<int:class_id>')
@admin_required
def class_rankings(class_id):
    class_obj = Class.query.get_or_404(class_id)
    rankings = generate_class_rankings(class_id)
    
    return render_template('admin/class_rankings.html', title=f'Rankings for {class_obj.name} - {class_obj.section}', class_obj=class_obj, rankings=rankings)

@admin.route('/top_students')
@admin_required
def top_students():
    top_students = generate_top_students()
    
    return render_template('admin/top_students.html', title='Top Students', top_students=top_students)

# Export routes
@admin.route('/export_students')
@admin_required
def export_students():
    csv_data = export_students_to_csv()
    
    return Response(
        csv_data,
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment;filename=students_{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}.csv'}
    )

@admin.route('/export_class_students/<int:class_id>')
@admin_required
def export_class_students(class_id):
    class_obj = Class.query.get_or_404(class_id)
    csv_data = export_students_to_csv(class_id=class_id)
    
    return Response(
        csv_data,
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment;filename=students_{class_obj.name}_{class_obj.section}_{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}.csv'}
    )

# Exams management
@admin.route('/exams', methods=['GET'])
@admin_required
def exams():
    # Get school_id for filtering
    school_id = None
    if current_user.admin_profile and current_user.admin_profile.school_id:
        school_id = current_user.admin_profile.school_id
    
    if school_id:
        # School-specific admin
        exams = Exam.query.join(Class).filter(Class.school_id==school_id).order_by(Exam.exam_date.desc()).all()
    else:
        # Super admin
        exams = Exam.query.order_by(Exam.exam_date.desc()).all()
    
    return render_template('admin/exams.html', title='Exams Management', exams=exams)

@admin.route('/exams/new', methods=['GET', 'POST'])
@admin_required
def create_exam():
    form = ExamForm()
    
    # Get school_id for filtering
    school_id = None
    if current_user.admin_profile and current_user.admin_profile.school_id:
        school_id = current_user.admin_profile.school_id
    
    # Populate teacher choices
    if school_id:
        # School-specific admin
        form.teacher_id.choices = [(t.id, t.full_name) for t in Teacher.query.filter_by(school_id=school_id).all()]
        # Pre-populate school field with current school name
        if request.method == 'GET':
            school = School.query.get(school_id)
            if school:
                form.school.data = school.name
    else:
        # Super admin
        form.teacher_id.choices = [(t.id, f"{t.full_name} ({t.school.name if t.school else 'No School'})") for t in Teacher.query.all()]
    
    if form.validate_on_submit():
        # Create a new exam with text input fields
        exam = Exam(
            title=form.title.data,
            description=form.description.data,
            exam_type=form.exam_type.data,
            class_id=None,  # We'll handle this differently
            subject_id=None,  # We'll handle this differently
            teacher_id=form.teacher_id.data,
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
                teacher_id=form.teacher_id.data,
                school_id=school_id
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
                teacher_id=form.teacher_id.data
            )
            db.session.add(new_subject)
            db.session.flush()  # Get the ID without committing
            exam.subject_id = new_subject.id
        
        db.session.add(exam)
        db.session.commit()
        
        flash(f'Exam "{form.title.data}" has been created successfully!', 'success')
        return redirect(url_for('admin.exams'))
    
    return render_template('admin/create_exam.html', title='Create New Exam', form=form)

@admin.route('/exams/<int:exam_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_exam(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    
    # Check if admin has access to this exam
    school_id = None
    if current_user.admin_profile and current_user.admin_profile.school_id:
        school_id = current_user.admin_profile.school_id
        
        # If school-specific admin, check if exam belongs to their school
        if school_id and exam.class_.school_id != school_id:
            flash('You do not have permission to edit this exam.', 'danger')
            return redirect(url_for('admin.exams'))
    
    form = ExamForm()
    
    # Populate form choices
    if school_id:
        # School-specific admin
        form.class_id.choices = [(c.id, f"{c.name} - {c.section}") for c in Class.query.filter_by(school_id=school_id).all()]
        form.teacher_id.choices = [(t.id, t.full_name) for t in Teacher.query.filter_by(school_id=school_id).all()]
    else:
        # Super admin
        form.class_id.choices = [(c.id, f"{c.name} - {c.section} ({c.school.name if c.school else 'No School'})") for c in Class.query.all()]
        form.teacher_id.choices = [(t.id, f"{t.full_name} ({t.school.name if t.school else 'No School'})") for t in Teacher.query.all()]
    
    # Populate subjects based on selected class
    form.subject_id.choices = [(s.id, s.name) for s in Subject.query.filter_by(class_id=exam.class_id).all()]
    
    if form.validate_on_submit():
        exam.title = form.title.data
        exam.description = form.description.data
        exam.exam_type = form.exam_type.data
        exam.subject_id = form.subject_id.data
        exam.class_id = form.class_id.data
        exam.teacher_id = form.teacher_id.data
        exam.total_marks = form.total_marks.data
        exam.passing_marks = form.passing_marks.data
        exam.exam_date = form.exam_date.data
        exam.status = form.status.data
        
        db.session.commit()
        
        flash(f'Exam "{exam.title}" has been updated successfully!', 'success')
        return redirect(url_for('admin.exams'))
    
    # Pre-populate form fields
    if request.method == 'GET':
        form.title.data = exam.title
        form.description.data = exam.description
        form.exam_type.data = exam.exam_type
        form.subject_id.data = exam.subject_id
        form.class_id.data = exam.class_id
        form.teacher_id.data = exam.teacher_id
        form.total_marks.data = exam.total_marks
        form.passing_marks.data = exam.passing_marks
        form.exam_date.data = exam.exam_date
        form.status.data = exam.status
    
    return render_template('admin/edit_exam.html', title='Edit Exam', form=form, exam=exam)

@admin.route('/exams/<int:exam_id>/delete', methods=['POST'])
@admin_required
def delete_exam(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    
    # Check if admin has access to this exam
    school_id = None
    if current_user.admin_profile and current_user.admin_profile.school_id:
        school_id = current_user.admin_profile.school_id
        
        # If school-specific admin, check if exam belongs to their school
        if school_id and exam.class_.school_id != school_id:
            flash('You do not have permission to delete this exam.', 'danger')
            return redirect(url_for('admin.exams'))
    
    db.session.delete(exam)
    db.session.commit()
    
    flash(f'Exam "{exam.title}" has been deleted successfully!', 'success')
    return redirect(url_for('admin.exams'))

@admin.route('/exams/<int:exam_id>', methods=['GET'])
@admin_required
def view_exam(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    
    # Check if admin has access to this exam
    school_id = None
    if current_user.admin_profile and current_user.admin_profile.school_id:
        school_id = current_user.admin_profile.school_id
        
        # If school-specific admin, check if exam belongs to their school
        if school_id and exam.class_.school_id != school_id:
            flash('You do not have permission to view this exam.', 'danger')
            return redirect(url_for('admin.exams'))
    
    # Get all marks for this exam
    marks = Mark.query.filter_by(exam_id=exam_id).all()
    
    # Calculate statistics
    total_students = Student.query.filter_by(class_id=exam.class_id).count()
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
    
    return render_template('admin/view_exam.html', 
                           title=f'Exam: {exam.title}',
                           exam=exam,
                           marks=marks,
                           total_students=total_students,
                           submitted_count=submitted_count,
                           pending_count=pending_count,
                           approved_count=approved_count,
                           avg_marks=avg_marks,
                           pass_percentage=pass_percentage)

@admin.route('/marks/<int:mark_id>/update-status', methods=['POST'])
@admin_required
def update_mark_status(mark_id):
    mark = Mark.query.get_or_404(mark_id)
    
    # Check if admin has access to this mark
    school_id = None
    if current_user.admin_profile and current_user.admin_profile.school_id:
        school_id = current_user.admin_profile.school_id
        
        # If school-specific admin, check if mark belongs to their school
        if school_id and mark.student.school_id != school_id:
            flash('You do not have permission to update this mark.', 'danger')
            return redirect(url_for('admin.exams'))
    
    status = request.form.get('status')
    if status not in ['approved', 'rejected']:
        flash('Invalid status.', 'danger')
        return redirect(url_for('admin.view_exam', exam_id=mark.exam_id))
    
    mark.status = status
    db.session.commit()
    
    flash(f'Mark has been {status}.', 'success')
    return redirect(url_for('admin.view_exam', exam_id=mark.exam_id))

@admin.route('/generate-rankings', methods=['GET', 'POST'])
@admin_required
def generate_rankings():
    if request.method == 'POST':
        academic_year = request.form.get('academic_year')
        term = request.form.get('term')
        
        # Get school_id for filtering
        school_id = None
        if current_user.admin_profile and current_user.admin_profile.school_id:
            school_id = current_user.admin_profile.school_id
        
        # Delete existing rankings for this academic year and term
        if school_id:
            Ranking.query.filter_by(school_id=school_id, academic_year=academic_year, term=term).delete()
        else:
            Ranking.query.filter_by(academic_year=academic_year, term=term).delete()
        
        # Get all classes
        if school_id:
            classes = Class.query.filter_by(school_id=school_id, academic_year=academic_year).all()
        else:
            classes = Class.query.filter_by(academic_year=academic_year).all()
        
        # Process each class
        for class_ in classes:
            # Get all students in this class
            students = Student.query.filter_by(class_id=class_.id).all()
            
            # Calculate total marks for each student
            student_marks = []
            for student in students:
                # Get all approved marks for this student
                marks = Mark.query.join(Exam).filter(
                    Mark.student_id == student.id,
                    Mark.status == 'approved',
                    Exam.class_id == class_.id
                ).all()
                
                # Calculate total marks and percentage
                total_obtained = sum(mark.marks_obtained for mark in marks)
                total_possible = sum(mark.exam.total_marks for mark in marks)
                
                percentage = (total_obtained / total_possible * 100) if total_possible > 0 else 0
                
                student_marks.append({
                    'student_id': student.id,
                    'total_marks': total_obtained,
                    'percentage': percentage
                })
            
            # Sort by percentage (descending)
            student_marks.sort(key=lambda x: x['percentage'], reverse=True)
            
            # Assign class ranks
            for i, student_mark in enumerate(student_marks, 1):
                student_mark['class_rank'] = i
            
            # Add to rankings
            for student_mark in student_marks:
                ranking = Ranking(
                    student_id=student_mark['student_id'],
                    class_id=class_.id,
                    school_id=class_.school_id,
                    academic_year=academic_year,
                    term=term,
                    total_marks=student_mark['total_marks'],
                    percentage=student_mark['percentage'],
                    class_rank=student_mark['class_rank'],
                    school_rank=0  # Will be updated later
                )
                db.session.add(ranking)
        
        # Commit to save class rankings
        db.session.commit()
        
        # Now calculate school rankings
        if school_id:
            # Get all rankings for this school, academic year, and term
            rankings = Ranking.query.filter_by(
                school_id=school_id,
                academic_year=academic_year,
                term=term
            ).order_by(Ranking.percentage.desc()).all()
            
            # Assign school ranks
            for i, ranking in enumerate(rankings, 1):
                ranking.school_rank = i
        else:
            # Process each school separately
            schools = School.query.all()
            for school in schools:
                # Get all rankings for this school, academic year, and term
                rankings = Ranking.query.filter_by(
                    school_id=school.id,
                    academic_year=academic_year,
                    term=term
                ).order_by(Ranking.percentage.desc()).all()
                
                # Assign school ranks
                for i, ranking in enumerate(rankings, 1):
                    ranking.school_rank = i
        
        # Commit to save school rankings
        db.session.commit()
        
        flash(f'Rankings for {academic_year} - {term} have been generated successfully!', 'success')
        return redirect(url_for('admin.view_rankings', academic_year=academic_year, term=term))
    
    # GET request - show form
    current_year = datetime.now().year
    academic_years = [str(year) + '-' + str(year + 1) for year in range(current_year - 5, current_year + 1)]
    
    return render_template('admin/generate_rankings.html', 
                           title='Generate Rankings',
                           academic_years=academic_years)

@admin.route('/rankings/<string:academic_year>/<string:term>', methods=['GET'])
@admin_required
def view_rankings(academic_year, term):
    # Get school_id for filtering
    school_id = None
    if current_user.admin_profile and current_user.admin_profile.school_id:
        school_id = current_user.admin_profile.school_id
    
    if school_id:
        # School-specific admin
        rankings = Ranking.query.filter_by(
            school_id=school_id,
            academic_year=academic_year,
            term=term
        ).order_by(Ranking.school_rank).all()
    else:
        # Super admin
        rankings = Ranking.query.filter_by(
            academic_year=academic_year,
            term=term
        ).order_by(Ranking.school_rank).all()
    
    return render_template('admin/view_rankings.html', 
                           title=f'Rankings: {academic_year} - {term}',
                           rankings=rankings,
                           academic_year=academic_year,
                           term=term)

@admin.route('/settings', methods=['GET', 'POST'])
@login_required
@admin_required
def settings():
    # Get the school settings
    school = School.query.first()
    if not school:
        school = School(name="Default School", academic_year="2023-2024", term="1", passing_percentage=40)
        db.session.add(school)
        db.session.commit()
    
    form = SettingsForm()
    account_form = AccountUpdateForm()
    restore_form = RestoreForm()
    
    # Pre-populate the form with current settings
    if request.method == 'GET':
        form.school_name.data = school.name
        form.academic_year.data = school.academic_year
        form.term.data = school.term
        form.passing_percentage.data = school.passing_percentage
        account_form.email.data = current_user.email
    
    # Handle form submission
    if form.validate_on_submit():
        school.name = form.school_name.data
        school.academic_year = form.academic_year.data
        school.term = form.term.data
        school.passing_percentage = form.passing_percentage.data
        db.session.commit()
        flash('Settings updated successfully!', 'success')
        return redirect(url_for('admin.settings'))
    
    return render_template('admin/settings.html', title='Settings', 
                          form=form, account_form=account_form, restore_form=restore_form)

@admin.route('/update_account', methods=['POST'])
@login_required
@admin_required
def update_account():
    form = AccountUpdateForm()
    if form.validate_on_submit():
        # Verify current password
        if bcrypt.check_password_hash(current_user.password, form.current_password.data):
            current_user.email = form.email.data
            # Update password if provided
            if form.new_password.data:
                current_user.password = bcrypt.generate_password_hash(form.new_password.data).decode('utf-8')
            db.session.commit()
            flash('Your account has been updated!', 'success')
        else:
            flash('Current password is incorrect!', 'danger')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{getattr(form, field).label.text}: {error}', 'danger')
    
    return redirect(url_for('admin.settings'))

@admin.route('/backup_database')
@login_required
@admin_required
def backup_database():
    # This is a placeholder for actual backup functionality
    # In a real application, you would create a database dump here
    flash('Database backup functionality is not implemented yet.', 'info')
    return redirect(url_for('admin.settings'))

@admin.route('/restore_database', methods=['POST'])
@login_required
@admin_required
def restore_database():
    form = RestoreForm()
    if form.validate_on_submit():
        # This is a placeholder for actual restore functionality
        # In a real application, you would restore from the uploaded file
        flash('Database restore functionality is not implemented yet.', 'info')
    return redirect(url_for('admin.settings'))

# School Management Routes for Master Admin
@admin.route('/manage-schools')
@login_required
@master_admin_required
def manage_schools():
    schools = School.query.all()
    return render_template('admin/manage_schools.html', title='Manage Schools', schools=schools)

@admin.route('/add-school', methods=['GET', 'POST'])
@login_required
@master_admin_required
def add_school():
    if request.method == 'POST':
        school_number = request.form.get('school_number')
        name = request.form.get('name')
        password = request.form.get('password')
        
        if School.query.filter_by(school_number=school_number).first():
            flash('School number already exists.', 'danger')
            return redirect(url_for('admin.add_school'))
        
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        school = School(
            school_number=school_number,
            name=name,
            password=hashed_password,
            address=request.form.get('address'),
            phone=request.form.get('phone'),
            email=request.form.get('email'),
            website=request.form.get('website')
        )
        
        db.session.add(school)
        db.session.commit()
        
        flash('School added successfully!', 'success')
        return redirect(url_for('admin.manage_schools'))
    
    return render_template('admin/add_school.html', title='Add New School')

@admin.route('/edit-school/<int:school_id>', methods=['GET', 'POST'])
@login_required
@master_admin_required
def edit_school(school_id):
    school = School.query.get_or_404(school_id)
    
    if request.method == 'POST':
        school.name = request.form.get('name')
        school.address = request.form.get('address')
        school.phone = request.form.get('phone')
        school.email = request.form.get('email')
        school.website = request.form.get('website')
        school.is_active = request.form.get('is_active') == 'on'
        
        if request.form.get('password'):
            school.password = bcrypt.generate_password_hash(request.form.get('password')).decode('utf-8')
        
        db.session.commit()
        flash('School updated successfully!', 'success')
        return redirect(url_for('admin.manage_schools'))
    
    return render_template('admin/edit_school.html', title='Edit School', school=school)

@admin.route('/delete-school/<int:school_id>')
@login_required
@master_admin_required
def delete_school(school_id):
    school = School.query.get_or_404(school_id)
    
    # Delete all associated data
    Admin.query.filter_by(school_id=school_id).delete()
    Teacher.query.filter_by(school_id=school_id).delete()
    Student.query.filter_by(school_id=school_id).delete()
    Class.query.filter_by(school_id=school_id).delete()
    
    db.session.delete(school)
    db.session.commit()
    
    flash('School deleted successfully!', 'success')
    return redirect(url_for('admin.manage_schools')) 