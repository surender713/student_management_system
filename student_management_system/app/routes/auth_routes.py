from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, current_user, logout_user, login_required
from app import db, bcrypt
from app.models import User, Admin, Teacher, Student, School, AdminRequest
from app.utils import user_exists
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField, TextAreaField, DateField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError

# Create blueprint
auth = Blueprint('auth', __name__)

# Login Form
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
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

# Login route
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            # Get the selected role from the form
            selected_role = request.form.get('role', '').strip()
            
            # Only check role if one was explicitly selected
            if selected_role and user.role != selected_role:
                flash(f'This email is not registered as a {selected_role}. Please select the correct role.', 'danger')
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
            flash('Login unsuccessful. Please check email and password.', 'danger')
    
    return render_template('login.html', title='Login', form=form)

# Logout route
@auth.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

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