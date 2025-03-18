from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import User, Student, Class, Subject, Mark, Attendance, Goal, Exam, TeacherNote, Question, Answer, Ranking
from app.utils import generate_subject_performance, generate_performance_trend, generate_class_rankings, student_required
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DateField, SubmitField, SelectField, FloatField
from wtforms.validators import DataRequired, Length, ValidationError
import datetime

# Create blueprint
student = Blueprint('student', __name__)

# Forms
class GoalForm(FlaskForm):
    title = StringField('Goal Title', validators=[DataRequired(), Length(min=2, max=100)])
    description = TextAreaField('Description')
    target_date = DateField('Target Date', validators=[DataRequired()])
    submit = SubmitField('Save Goal')

# Routes
@student.route('/dashboard')
@student_required
def dashboard():
    # Get student profile
    student_profile = Student.query.filter_by(user_id=current_user.id).first()
    
    if not student_profile:
        flash('Student profile not found. Please contact the administrator.', 'danger')
        return redirect(url_for('auth.logout'))
    
    # Get class information
    class_obj = Class.query.get(student_profile.class_id)
    
    # Get performance data
    performance = generate_subject_performance(student_profile.id)
    
    # Generate performance trend graph
    trend_graph = generate_performance_trend(student_profile.id)
    
    # Get class ranking
    rankings = generate_class_rankings(student_profile.class_id)
    student_rank = None
    
    if not rankings.empty:
        student_row = rankings[rankings['student_id'] == student_profile.id]
        if not student_row.empty:
            student_rank = student_row['rank'].values[0]
    
    # Get recent marks
    recent_marks = []
    marks = Mark.query.filter_by(student_id=student_profile.id).order_by(Mark.created_at.desc()).limit(5).all()
    
    for mark in marks:
        subject = Subject.query.get(mark.subject_id)
        exam = Exam.query.get(mark.exam_id)
        recent_marks.append({
            'subject_name': subject.name,
            'exam_type': exam.exam_type,
            'marks_obtained': mark.marks_obtained,
            'total_marks': exam.total_marks,
            'percentage': round(mark.marks_obtained / exam.total_marks * 100, 2),
            'date': mark.created_at
        })
    
    # Get recent attendance
    recent_attendance = Attendance.query.filter_by(student_id=student_profile.id).order_by(Attendance.date.desc()).limit(5).all()
    
    # Get goals
    goals = Goal.query.filter_by(student_id=student_profile.id).order_by(Goal.target_date).all()
    
    return render_template('student/dashboard.html', 
                           title='Student Dashboard',
                           student=student_profile,
                           class_obj=class_obj,
                           performance=performance,
                           trend_graph=trend_graph,
                           student_rank=student_rank,
                           total_students=len(rankings) if not rankings.empty else 0,
                           recent_marks=recent_marks,
                           recent_attendance=recent_attendance,
                           goals=goals)

# Performance routes
@student.route('/performance')
@student_required
def performance():
    # Get student profile
    student_profile = Student.query.filter_by(user_id=current_user.id).first()
    
    # Get performance data
    performance = generate_subject_performance(student_profile.id)
    
    # Generate performance trend graph
    trend_graph = generate_performance_trend(student_profile.id)
    
    return render_template('student/performance.html', 
                           title='My Performance',
                           student=student_profile,
                           performance=performance,
                           trend_graph=trend_graph)

@student.route('/subject_performance/<int:subject_id>')
@student_required
def subject_performance(subject_id):
    # Get student profile
    student_profile = Student.query.filter_by(user_id=current_user.id).first()
    
    # Get subject
    subject = Subject.query.get_or_404(subject_id)
    
    # Get subject marks
    subject_marks = []
    marks = Mark.query.filter_by(student_id=student_profile.id, subject_id=subject_id).order_by(Mark.created_at).all()
    
    for mark in marks:
        exam = Exam.query.get(mark.exam_id)
        subject_marks.append({
            'id': mark.id,
            'exam_type': exam.exam_type,
            'marks_obtained': mark.marks_obtained,
            'total_marks': exam.total_marks,
            'percentage': round(mark.marks_obtained / exam.total_marks * 100, 2),
            'date': mark.created_at.strftime('%d-%m-%Y'),
            'status': mark.status
        })
    
    # Calculate statistics
    total_marks = len(marks)
    if total_marks > 0:
        avg_percentage = sum(mark.marks_obtained / mark.total_marks * 100 for mark in marks) / total_marks
    else:
        avg_percentage = 0
    
    return render_template('student/subject_performance.html', 
                           title=f'Performance in {subject.name}',
                           student=student_profile,
                           subject=subject,
                           marks=subject_marks,
                           avg_percentage=round(avg_percentage, 2),
                           total_marks=total_marks)

# Ranking routes
@student.route('/class_ranking')
@student_required
def class_ranking():
    # Get student profile
    student_profile = Student.query.filter_by(user_id=current_user.id).first()
    
    # Get class information
    class_obj = Class.query.get(student_profile.class_id)
    
    # Generate rankings
    rankings = generate_class_rankings(student_profile.class_id)
    
    # Get student rank
    student_rank = None
    
    if not rankings.empty:
        student_row = rankings[rankings['student_id'] == student_profile.id]
        if not student_row.empty:
            student_rank = student_row['rank'].values[0]
    
    return render_template('student/class_ranking.html', 
                           title='Class Ranking',
                           student=student_profile,
                           class_obj=class_obj,
                           rankings=rankings,
                           student_rank=student_rank)

# Attendance routes
@student.route('/attendance')
@student_required
def attendance():
    # Get student profile
    student_profile = Student.query.filter_by(user_id=current_user.id).first()
    
    # Get attendance records
    attendance_records = Attendance.query.filter_by(student_id=student_profile.id).order_by(Attendance.date.desc()).all()
    
    # Calculate statistics
    total_records = len(attendance_records)
    present_count = sum(1 for record in attendance_records if record.status == 'present')
    absent_count = sum(1 for record in attendance_records if record.status == 'absent')
    late_count = sum(1 for record in attendance_records if record.status == 'late')
    
    if total_records > 0:
        present_percentage = (present_count / total_records) * 100
        absent_percentage = (absent_count / total_records) * 100
        late_percentage = (late_count / total_records) * 100
    else:
        present_percentage = absent_percentage = late_percentage = 0
    
    return render_template('student/attendance.html', 
                           title='My Attendance',
                           student=student_profile,
                           attendance_records=attendance_records,
                           total_records=total_records,
                           present_count=present_count,
                           absent_count=absent_count,
                           late_count=late_count,
                           present_percentage=round(present_percentage, 2),
                           absent_percentage=round(absent_percentage, 2),
                           late_percentage=round(late_percentage, 2))

# Goal routes
@student.route('/goals')
@student_required
def goals():
    # Get student profile
    student_profile = Student.query.filter_by(user_id=current_user.id).first()
    
    # Get goals
    goals = Goal.query.filter_by(student_id=student_profile.id).order_by(Goal.target_date).all()
    
    # Separate goals by status
    in_progress_goals = [goal for goal in goals if goal.status == 'in_progress']
    completed_goals = [goal for goal in goals if goal.status == 'completed']
    missed_goals = [goal for goal in goals if goal.status == 'missed']
    
    return render_template('student/goals.html', 
                           title='My Goals',
                           student=student_profile,
                           in_progress_goals=in_progress_goals,
                           completed_goals=completed_goals,
                           missed_goals=missed_goals)

@student.route('/add_goal', methods=['GET', 'POST'])
@student_required
def add_goal():
    # Get student profile
    student_profile = Student.query.filter_by(user_id=current_user.id).first()
    
    form = GoalForm()
    
    if form.validate_on_submit():
        goal = Goal(
            student_id=student_profile.id,
            title=form.title.data,
            description=form.description.data,
            target_date=form.target_date.data,
            status='in_progress'
        )
        
        db.session.add(goal)
        db.session.commit()
        
        flash(f'Goal "{form.title.data}" has been set!', 'success')
        return redirect(url_for('student.goals'))
    
    return render_template('student/add_goal.html', title='Set a New Goal', form=form)

@student.route('/edit_goal/<int:goal_id>', methods=['GET', 'POST'])
@student_required
def edit_goal(goal_id):
    # Get student profile
    student_profile = Student.query.filter_by(user_id=current_user.id).first()
    
    # Get goal
    goal = Goal.query.get_or_404(goal_id)
    
    # Check if the goal belongs to the student
    if goal.student_id != student_profile.id:
        flash('You do not have permission to edit this goal.', 'danger')
        return redirect(url_for('student.goals'))
    
    form = GoalForm()
    
    if form.validate_on_submit():
        goal.title = form.title.data
        goal.description = form.description.data
        goal.target_date = form.target_date.data
        
        db.session.commit()
        
        flash(f'Goal "{form.title.data}" has been updated!', 'success')
        return redirect(url_for('student.goals'))
    
    # Populate form
    form.title.data = goal.title
    form.description.data = goal.description
    form.target_date.data = goal.target_date
    
    return render_template('student/edit_goal.html', title='Edit Goal', form=form, goal=goal)

@student.route('/complete_goal/<int:goal_id>', methods=['POST'])
@student_required
def complete_goal(goal_id):
    # Get student profile
    student_profile = Student.query.filter_by(user_id=current_user.id).first()
    
    # Get goal
    goal = Goal.query.get_or_404(goal_id)
    
    # Check if the goal belongs to the student
    if goal.student_id != student_profile.id:
        flash('You do not have permission to update this goal.', 'danger')
        return redirect(url_for('student.goals'))
    
    goal.status = 'completed'
    db.session.commit()
    
    flash(f'Goal "{goal.title}" marked as completed!', 'success')
    return redirect(url_for('student.goals'))

@student.route('/delete_goal/<int:goal_id>', methods=['POST'])
@student_required
def delete_goal(goal_id):
    # Get student profile
    student_profile = Student.query.filter_by(user_id=current_user.id).first()
    
    # Get goal
    goal = Goal.query.get_or_404(goal_id)
    
    # Check if the goal belongs to the student
    if goal.student_id != student_profile.id:
        flash('You do not have permission to delete this goal.', 'danger')
        return redirect(url_for('student.goals'))
    
    db.session.delete(goal)
    db.session.commit()
    
    flash('Goal has been deleted!', 'success')
    return redirect(url_for('student.goals'))

# Top student insights
@student.route('/top_student_insights')
@student_required
def top_student_insights():
    # Get student profile
    student_profile = Student.query.filter_by(user_id=current_user.id).first()
    
    # Get class information
    class_obj = Class.query.get(student_profile.class_id)
    
    # Generate rankings
    rankings = generate_class_rankings(student_profile.class_id)
    
    # Get top 3 students
    top_students = []
    
    if not rankings.empty and len(rankings) >= 3:
        for i in range(3):
            student_id = rankings.iloc[i]['student_id']
            student = Student.query.get(student_id)
            
            # Get attendance statistics
            attendance_records = Attendance.query.filter_by(student_id=student_id).all()
            present_count = sum(1 for record in attendance_records if record.status == 'present')
            total_records = len(attendance_records)
            attendance_percentage = (present_count / total_records * 100) if total_records > 0 else 0
            
            # Get marks statistics
            marks = Mark.query.filter_by(student_id=student_id).all()
            avg_percentage = rankings.iloc[i]['average_percentage']
            
            top_students.append({
                'name': student.full_name,
                'rank': i + 1,
                'average_percentage': avg_percentage,
                'attendance_percentage': round(attendance_percentage, 2)
            })
    
    return render_template('student/top_student_insights.html', 
                           title='Top Student Insights',
                           student=student_profile,
                           class_obj=class_obj,
                           top_students=top_students)

# Subjects
@student.route('/subjects')
@student_required
def subjects():
    # Get student profile
    student_profile = Student.query.filter_by(user_id=current_user.id).first()
    
    # Get subjects for student's class
    subjects = Subject.query.filter_by(class_id=student_profile.class_id).all()
    
    return render_template('student/subjects.html', title='My Subjects', subjects=subjects)

# Subject details
@student.route('/subjects/<int:subject_id>')
@student_required
def subject_details(subject_id):
    # Get student profile
    student_profile = Student.query.filter_by(user_id=current_user.id).first()
    
    # Get subject
    subject = Subject.query.get_or_404(subject_id)
    
    # Check if student has access to this subject
    if subject.class_id != student_profile.class_id:
        flash('You do not have access to this subject.', 'danger')
        return redirect(url_for('student.subjects'))
    
    # Get exams for this subject
    exams = Exam.query.filter_by(subject_id=subject_id).order_by(Exam.exam_date.desc()).all()
    
    # Get marks for this subject
    marks = Mark.query.filter_by(student_id=student_profile.id, subject_id=subject_id).all()
    
    # Get notes for this subject
    notes = TeacherNote.query.filter_by(subject_id=subject_id).order_by(TeacherNote.created_at.desc()).all()
    
    # Get questions for this subject
    questions = Question.query.filter_by(subject_id=subject_id).order_by(Question.created_at.desc()).all()
    
    return render_template('student/subject_details.html', 
                           title=f'Subject: {subject.name}',
                           subject=subject,
                           exams=exams,
                           marks=marks,
                           notes=notes,
                           questions=questions)

# Exams
@student.route('/exams')
@student_required
def exams():
    # Get student profile
    student_profile = Student.query.filter_by(user_id=current_user.id).first()
    
    # Get all exams for student's class
    exams = Exam.query.filter_by(class_id=student_profile.class_id).order_by(Exam.exam_date.desc()).all()
    
    # Get marks for each exam
    marks = {mark.exam_id: mark for mark in Mark.query.filter_by(student_id=student_profile.id).all()}
    
    return render_template('student/exams.html', title='My Exams', exams=exams, marks=marks)

# Exam details
@student.route('/exams/<int:exam_id>')
@student_required
def exam_details(exam_id):
    # Get student profile
    student_profile = Student.query.filter_by(user_id=current_user.id).first()
    
    # Get exam
    exam = Exam.query.get_or_404(exam_id)
    
    # Check if student has access to this exam
    if exam.class_id != student_profile.class_id:
        flash('You do not have access to this exam.', 'danger')
        return redirect(url_for('student.exams'))
    
    # Get mark for this exam
    mark = Mark.query.filter_by(student_id=student_profile.id, exam_id=exam_id).first()
    
    return render_template('student/exam_details.html', 
                           title=f'Exam: {exam.title}',
                           exam=exam,
                           mark=mark)

# Submit marks form
class SubmitMarkForm(FlaskForm):
    marks_obtained = FloatField('Marks Obtained', validators=[DataRequired()])
    remarks = TextAreaField('Remarks')
    submit = SubmitField('Submit Marks')

# Submit marks for an exam
@student.route('/exams/<int:exam_id>/submit-marks', methods=['GET', 'POST'])
@student_required
def submit_marks(exam_id):
    # Get student profile
    student_profile = Student.query.filter_by(user_id=current_user.id).first()
    
    # Get exam
    exam = Exam.query.get_or_404(exam_id)
    
    # Check if student has access to this exam
    if exam.class_id != student_profile.class_id:
        flash('You do not have access to this exam.', 'danger')
        return redirect(url_for('student.exams'))
    
    # Check if marks already submitted
    existing_mark = Mark.query.filter_by(student_id=student_profile.id, exam_id=exam_id).first()
    if existing_mark:
        flash('You have already submitted marks for this exam.', 'info')
        return redirect(url_for('student.exam_details', exam_id=exam_id))
    
    # Check if exam is completed
    if exam.status != 'completed':
        flash('You can only submit marks for completed exams.', 'warning')
        return redirect(url_for('student.exam_details', exam_id=exam_id))
    
    form = SubmitMarkForm()
    
    if form.validate_on_submit():
        # Check if marks are within range
        if form.marks_obtained.data > exam.total_marks:
            flash(f'Marks obtained cannot be greater than total marks ({exam.total_marks}).', 'danger')
            return render_template('student/submit_marks.html', title='Submit Marks', form=form, exam=exam)
        
        mark = Mark(
            student_id=student_profile.id,
            subject_id=exam.subject_id,
            exam_id=exam.id,
            marks_obtained=form.marks_obtained.data,
            remarks=form.remarks.data,
            submitted_by='student',
            status='pending'  # Student-submitted marks need approval
        )
        
        db.session.add(mark)
        db.session.commit()
        
        flash('Your marks have been submitted and are pending approval.', 'success')
        return redirect(url_for('student.exam_details', exam_id=exam_id))
    
    return render_template('student/submit_marks.html', title='Submit Marks', form=form, exam=exam)

# Marks
@student.route('/marks')
@student_required
def marks():
    # Get student profile
    student_profile = Student.query.filter_by(user_id=current_user.id).first()
    
    # Get all marks for this student
    marks = Mark.query.filter_by(student_id=student_profile.id).all()
    
    # Group marks by subject
    subjects = Subject.query.filter_by(class_id=student_profile.class_id).all()
    marks_by_subject = {subject.id: [] for subject in subjects}
    
    for mark in marks:
        if mark.subject_id in marks_by_subject:
            marks_by_subject[mark.subject_id].append(mark)
    
    # Calculate subject-wise performance
    subject_performance = {}
    for subject_id, subject_marks in marks_by_subject.items():
        if subject_marks:
            total_obtained = sum(mark.marks_obtained for mark in subject_marks if mark.status == 'approved')
            total_possible = sum(mark.exam.total_marks for mark in subject_marks if mark.status == 'approved')
            
            if total_possible > 0:
                percentage = (total_obtained / total_possible) * 100
                subject_performance[subject_id] = {
                    'total_obtained': total_obtained,
                    'total_possible': total_possible,
                    'percentage': percentage
                }
    
    return render_template('student/marks.html', 
                           title='My Marks',
                           student=student_profile,
                           subjects=subjects,
                           marks_by_subject=marks_by_subject,
                           subject_performance=subject_performance)

# Notes
@student.route('/notes')
@student_required
def notes():
    # Get student profile
    student_profile = Student.query.filter_by(user_id=current_user.id).first()
    
    # Get all notes for student's class subjects
    notes = TeacherNote.query.join(Subject).filter(Subject.class_id==student_profile.class_id).order_by(TeacherNote.created_at.desc()).all()
    
    # Group notes by subject
    subjects = Subject.query.filter_by(class_id=student_profile.class_id).all()
    notes_by_subject = {subject.id: [] for subject in subjects}
    
    for note in notes:
        if note.subject_id in notes_by_subject:
            notes_by_subject[note.subject_id].append(note)
    
    return render_template('student/notes.html', 
                           title='Notes',
                           notes=notes,
                           subjects=subjects,
                           notes_by_subject=notes_by_subject)

# Q&A routes
@student.route('/questions')
@student_required
def questions():
    # Get student profile
    student_profile = Student.query.filter_by(user_id=current_user.id).first()
    
    # Get all questions asked by this student
    my_questions = Question.query.filter_by(student_id=student_profile.id).order_by(Question.created_at.desc()).all()
    
    # Get class subjects
    subjects = Subject.query.filter_by(class_id=student_profile.class_id).all()
    
    return render_template('student/questions.html', 
                           title='My Questions',
                           student=student_profile,
                           my_questions=my_questions,
                           subjects=subjects)

# Question Form
class QuestionForm(FlaskForm):
    subject_id = SelectField('Subject', coerce=int, validators=[DataRequired()])
    title = StringField('Question Title', validators=[DataRequired(), Length(min=2, max=100)])
    content = TextAreaField('Question Details', validators=[DataRequired()])
    submit = SubmitField('Submit Question')

@student.route('/ask_question', methods=['GET', 'POST'])
@student_required
def ask_question():
    # Get student profile
    student_profile = Student.query.filter_by(user_id=current_user.id).first()
    
    form = QuestionForm()
    
    # Populate subject choices
    form.subject_id.choices = [(s.id, s.name) for s in Subject.query.filter_by(class_id=student_profile.class_id).all()]
    
    if form.validate_on_submit():
        question = Question(
            student_id=student_profile.id,
            subject_id=form.subject_id.data,
            title=form.title.data,
            content=form.content.data,
            status='open'
        )
        
        db.session.add(question)
        db.session.commit()
        
        flash('Your question has been submitted!', 'success')
        return redirect(url_for('student.questions'))
    
    return render_template('student/ask_question.html', 
                           title='Ask a Question',
                           form=form)

@student.route('/questions/<int:question_id>', methods=['GET', 'POST'])
@student_required
def question_details(question_id):
    # Get student profile
    student_profile = Student.query.filter_by(user_id=current_user.id).first()
    
    # Get question
    question = Question.query.get_or_404(question_id)
    
    # Check if the question belongs to the student
    if question.student_id != student_profile.id:
        flash('You do not have permission to view this question.', 'danger')
        return redirect(url_for('student.questions'))
    
    # Get all answers for this question
    answers = Answer.query.filter_by(question_id=question_id).order_by(Answer.created_at).all()
    
    # Process form submission (new answer/reply)
    if request.method == 'POST':
        content = request.form.get('content')
        
        if content:
            answer = Answer(
                question_id=question_id,
                user_id=current_user.id,
                content=content
            )
            
            db.session.add(answer)
            db.session.commit()
            
            flash('Your reply has been posted!', 'success')
            return redirect(url_for('student.question_details', question_id=question_id))
    
    return render_template('student/question_details.html', 
                           title=f'Question: {question.title}',
                           question=question,
                           answers=answers)

@student.route('/close_question/<int:question_id>', methods=['POST'])
@student_required
def close_question(question_id):
    # Get student profile
    student_profile = Student.query.filter_by(user_id=current_user.id).first()
    
    # Get question
    question = Question.query.get_or_404(question_id)
    
    # Check if the question belongs to the student
    if question.student_id != student_profile.id:
        flash('You do not have permission to close this question.', 'danger')
        return redirect(url_for('student.questions'))
    
    question.status = 'closed'
    db.session.commit()
    
    flash('Question has been closed!', 'success')
    return redirect(url_for('student.questions')) 