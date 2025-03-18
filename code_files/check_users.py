from app import create_app, db
from app.models import User, Admin, Teacher, Student

app = create_app()

def check_users():
    with app.app_context():
        # Check all users
        users = User.query.all()
        print(f"Total users: {len(users)}")
        
        # Check users by role
        admin_users = User.query.filter_by(role='admin').all()
        teacher_users = User.query.filter_by(role='teacher').all()
        student_users = User.query.filter_by(role='student').all()
        
        print(f"Admin users: {len(admin_users)}")
        print(f"Teacher users: {len(teacher_users)}")
        print(f"Student users: {len(student_users)}")
        
        # Print admin details
        if admin_users:
            print("\nAdmin details:")
            for user in admin_users:
                print(f"ID: {user.id}, Username: {user.username}, Email: {user.email}")
                admin = Admin.query.filter_by(user_id=user.id).first()
                if admin:
                    print(f"  Admin profile: {admin.full_name}, School ID: {admin.school_id}")
                else:
                    print("  No admin profile found!")
        else:
            print("\nNo admin users found!")

if __name__ == "__main__":
    check_users() 