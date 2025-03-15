from app import create_app, db, bcrypt
from app.models import User, Admin
from flask_login import login_user
import sys

def check_login():
    app = create_app()
    with app.app_context():
        # Get admin user
        admin_user = User.query.filter_by(role='admin').first()
        
        if not admin_user:
            print("No admin user found in the database.")
            return
        
        print(f"Found admin user: {admin_user.username} ({admin_user.email})")
        
        # Test password
        test_password = "admin123"  # Replace with the password you're trying
        password_valid = bcrypt.check_password_hash(admin_user.password, test_password)
        
        print(f"Password '{test_password}' is valid: {password_valid}")
        
        if password_valid:
            # Check if there's an admin profile
            admin_profile = Admin.query.filter_by(user_id=admin_user.id).first()
            if admin_profile:
                print(f"Admin profile found: {admin_profile.full_name}")
            else:
                print("No admin profile found for this user.")
        
        # Try another password if the first one doesn't work
        if not password_valid:
            alt_password = "password"  # Another common default password
            alt_valid = bcrypt.check_password_hash(admin_user.password, alt_password)
            print(f"Alternative password '{alt_password}' is valid: {alt_valid}")

if __name__ == "__main__":
    check_login() 