from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, current_user, logout_user, login_required
from app import db, bcrypt
from app.models import User, Admin, Teacher, Student, School, AdminRequest, MasterAdmin
from app.utils import user_exists
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField, TextAreaField, DateField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError

# Create blueprint
auth = Blueprint('auth', __name__)

# School Login Form
class SchoolLoginForm(FlaskForm):
    school_number = StringField('School Number', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

# Master Admin Login Form
class MasterAdminLoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

# Login Form - Changed to use username instead of email
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

# Registration Form for Students and Teachers
class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    full_name = StringField('Full Name', validators=[DataRequired()])
    phone = StringField('Phone Number')
    school_id = SelectField('School', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Sign Up')
    
    def validate_username(self, username):
        if user_exists(username=username.data):
            raise ValidationError('That username is already taken. Please choose a different one.')
    
    def validate_email(self, email):
        if user_exists(email=email.data):
            raise ValidationError('That email is already registered. Please use a different one.')

# Student Registration Form
class StudentRegistrationForm(RegistrationForm):
    roll_number = StringField('Roll Number', validators=[DataRequired()])
    date_of_birth = DateField('Date of Birth', validators=[DataRequired()])
    gender = SelectField('Gender', choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')], validators=[DataRequired()])
    parent_name = StringField('Parent Name')
    parent_phone = StringField('Parent Phone')
    class_id = SelectField('Class', coerce=int, validators=[DataRequired()])

# Teacher Registration Form
class TeacherRegistrationForm(RegistrationForm):
    qualification = StringField('Qualification', validators=[DataRequired()])
    department = StringField('Department', validators=[DataRequired()])
    experience = StringField('Years of Experience')

# Admin Request Form
class AdminRequestForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    full_name = StringField('Full Name', validators=[DataRequired()])
    phone = StringField('Phone Number', validators=[DataRequired()])
    school_id = SelectField('School', coerce=int, validators=[DataRequired()])
    reason = TextAreaField('Reason for Admin Access', validators=[DataRequired()])
    submit = SubmitField('Submit Request')
    
    def validate_username(self, username):
        if user_exists(username=username.data):
            raise ValidationError('That username is already taken. Please choose a different one.')
    
    def validate_email(self, email):
        if user_exists(email=email.data):
            raise ValidationError('That email is already registered. Please use a different one.')

# School login route
@auth.route('/school-login', methods=['GET', 'POST'])
def school_login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    
    form = SchoolLoginForm()
    
    if form.validate_on_submit():
        school = School.query.filter_by(school_number=form.school_number.data).first()
        
        if school and school.is_active and bcrypt.check_password_hash(school.password, form.password.data):
            # Store school info in session
            session['school_id'] = school.id
            session['school_name'] = school.name
            flash(f'Welcome to {school.name}! Please login with your credentials.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('Invalid school number or password. Please try again.', 'danger')
    
    return render_template('school_login.html', title='School Login', form=form)

# Master Admin login route
@auth.route('/master-admin-login', methods=['GET', 'POST'])
def master_admin_login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    
    form = MasterAdminLoginForm()
    
    if form.validate_on_submit():
        master_admin = MasterAdmin.query.filter_by(username=form.username.data).first()
        
        if master_admin and bcrypt.check_password_hash(master_admin.password, form.password.data):
            # Check if a User record already exists for this master admin
            user = User.query.filter_by(username=master_admin.username).first()
            
            # If user doesn't exist, create one
            if not user:
                user = User(
                    username=master_admin.username,
                    email=master_admin.email,
                    password=master_admin.password,  # Already hashed
                    role='master_admin'
                )
                db.session.add(user)
                db.session.commit()
            elif user.role != 'master_admin':
                # Update role if it's not set correctly
                user.role = 'master_admin'
                db.session.commit()
                
            login_user(user)
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('admin.manage_schools'))
        else:
            flash('Invalid username or password. Please try again.', 'danger')
    
    return render_template('master_admin_login.html', title='Master Admin Login', form=form)

# Update the existing login route to use username instead of email
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    
    # Check if school is selected
    if 'school_id' not in session:
        flash('Please login to your school first.', 'warning')
        return redirect(url_for('auth.school_login'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            # Check if user belongs to the selected school
            if user.role == 'admin':
                admin = Admin.query.filter_by(user_id=user.id).first()
                if admin and admin.school_id != session['school_id']:
                    flash('You do not have access to this school.', 'danger')
                    return render_template('login.html', title='Login', form=form)
            elif user.role == 'teacher':
                teacher = Teacher.query.filter_by(user_id=user.id).first()
                if teacher and teacher.school_id != session['school_id']:
                    flash('You do not have access to this school.', 'danger')
                    return render_template('login.html', title='Login', form=form)
            elif user.role == 'student':
                student = Student.query.filter_by(user_id=user.id).first()
                if student and student.school_id != session['school_id']:
                    flash('You do not have access to this school.', 'danger')
                    return render_template('login.html', title='Login', form=form)
            
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            
            # Redirect based on user role
            if user.role == 'admin':
                return redirect(next_page) if next_page else redirect(url_for('admin.dashboard'))
            elif user.role == 'teacher':
                return redirect(next_page) if next_page else redirect(url_for('teacher.dashboard'))
            else:  # student
                return redirect(next_page) if next_page else redirect(url_for('student.dashboard'))
        else:
            flash('Login unsuccessful. Please check username and password.', 'danger')
    
    return render_template('login.html', title='Login', form=form)

# Update logout route to clear school session
@auth.route('/logout')
def logout():
    logout_user()
    session.clear()  # Clear all session data including school info
    return redirect(url_for('auth.school_login'))

# Registration route for students and teachers
@auth.route('/register/<string:role>', methods=['GET', 'POST'])
def register(role):
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    
    if role == 'student':
        form = StudentRegistrationForm()
        # Get all schools for the form dropdown
        form.school_id.choices = [(s.id, s.name) for s in School.query.all()]
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
                address=form.address.data if hasattr(form, 'address') else None,
                phone=form.phone.data,
                parent_name=form.parent_name.data,
                parent_phone=form.parent_phone.data,
                class_id=form.class_id.data,
                school_id=form.school_id.data
            )
            
            db.session.add(student)
            db.session.commit()
            
            flash(f'Account created for {form.username.data}! You can now log in.', 'success')
            return redirect(url_for('auth.login'))
        
        return render_template('register_student.html', title='Register as Student', form=form)
    
    elif role == 'teacher':
        form = TeacherRegistrationForm()
        # Get all schools for the form dropdown
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
                school_id=form.school_id.data
            )
            
            db.session.add(teacher)
            db.session.commit()
            
            flash(f'Account created for {form.username.data}! You can now log in.', 'success')
            return redirect(url_for('auth.login'))
        
        return render_template('register_teacher.html', title='Register as Teacher', form=form)
    
    else:
        flash('Invalid registration type.', 'danger')
        return redirect(url_for('auth.login'))

# Admin request route
@auth.route('/register_admin_request', methods=['GET', 'POST'])
def register_admin_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    
    form = AdminRequestForm()
    # Get all schools for the form dropdown
    form.school_id.choices = [(s.id, s.name) for s in School.query.all()]
    
    if form.validate_on_submit():
        # Create admin request
        admin_request = AdminRequest(
            username=form.username.data,
            email=form.email.data,
            full_name=form.full_name.data,
            phone=form.phone.data,
            school_id=form.school_id.data,
            reason=form.reason.data,
            status='pending'
        )
        
        db.session.add(admin_request)
        db.session.commit()
        
        flash('Your admin access request has been submitted and is pending approval.', 'info')
        return redirect(url_for('auth.login'))
    
    return render_template('register_admin_request.html', title='Request Admin Access', form=form)

# Password reset request route (to be implemented)
@auth.route('/reset_password', methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    
    # To be implemented
    return render_template('reset_request.html', title='Reset Password')

# Password reset route (to be implemented)
@auth.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    
    # To be implemented
    return render_template('reset_token.html', title='Reset Password') 