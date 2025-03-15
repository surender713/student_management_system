from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user, login_required

# Create blueprint
main = Blueprint('main', __name__)

# Home route
@main.route('/')
@main.route('/home')
def home():
    if current_user.is_authenticated:
        # Redirect based on user role
        if current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif current_user.role == 'teacher':
            return redirect(url_for('teacher.dashboard'))
        else:  # student
            return redirect(url_for('student.dashboard'))
    
    # If not authenticated, show landing page
    return render_template('index.html', title='Home')

# About route
@main.route('/about')
def about():
    return render_template('about.html', title='About')

# Contact route
@main.route('/contact')
def contact():
    return render_template('contact.html', title='Contact')

# Error handlers
@main.app_errorhandler(404)
def error_404(error):
    return render_template('errors/404.html'), 404

@main.app_errorhandler(403)
def error_403(error):
    return render_template('errors/403.html'), 403

@main.app_errorhandler(500)
def error_500(error):
    return render_template('errors/500.html'), 500 