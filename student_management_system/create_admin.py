from app import create_app, db, bcrypt
from app.models import User, Admin, School

def create_admin():
    app = create_app()
    with app.app_context():
        # Check if admin exists
        admin_user = User.query.filter_by(email='admin@example.com').first()
        
        if admin_user:
            print("Admin user already exists.")
            return
        
        # Get the first school
        school = School.query.first()
        if not school:
            print("No schools found in the database.")
            return
        
        # Create user
        hashed_password = bcrypt.generate_password_hash('admin123').decode('utf-8')
        user = User(
            username='admin',
            email='admin@example.com',
            password=hashed_password,
            role='admin'
        )
        
        db.session.add(user)
        db.session.commit()
        
        # Create admin profile
        admin = Admin(
            user_id=user.id,
            full_name='System Administrator',
            school_id=school.id
        )
        
        db.session.add(admin)
        db.session.commit()
        
        print("Admin user created successfully!")
        print("Username: admin")
        print("Email: admin@example.com")
        print("Password: admin123")

if __name__ == "__main__":
    create_admin() 