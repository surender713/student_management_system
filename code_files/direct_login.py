from app import create_app, db, bcrypt
from app.models import User, Admin, School

def direct_login():
    app = create_app()
    with app.app_context():
        # Check if admin already exists
        admin_user = User.query.filter_by(email="admin@example.com").first()
        
        if not admin_user:
            # Get the first school
            school = School.query.first()
            if not school:
                print("No school found. Please create a school first.")
                return
            
            # Create admin user
            hashed_password = bcrypt.generate_password_hash("admin123").decode('utf-8')
            admin_user = User(
                username="admin_direct",
                email="admin@example.com",
                password=hashed_password,
                role='admin'
            )
            
            db.session.add(admin_user)
            db.session.commit()
            
            # Create admin profile
            admin = Admin(
                user_id=admin_user.id,
                full_name="Direct Login Admin",
                school_id=school.id
            )
            
            db.session.add(admin)
            db.session.commit()
        
        print("Admin user exists.")
        print("To log in, use the following credentials:")
        print("Email: admin@example.com")
        print("Password: admin123")
        print("\nIMPORTANT: When logging in, make sure to:")
        print("1. Click on the 'Admin' role card")
        print("2. Enter the email and password exactly as shown above")
        print("3. Click the 'Login' button")
        
        # Update the password to make sure it's correct
        hashed_password = bcrypt.generate_password_hash("admin123").decode('utf-8')
        admin_user.password = hashed_password
        db.session.commit()
        print("\nPassword has been reset to 'admin123'")

if __name__ == "__main__":
    direct_login() 