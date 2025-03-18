from app import create_app, db, bcrypt
from app.models import User, Admin

def fix_login():
    app = create_app()
    with app.app_context():
        # Get all admin users
        admin_users = User.query.filter_by(role='admin').all()
        
        print(f"Found {len(admin_users)} admin users:")
        for admin in admin_users:
            print(f"- {admin.username} ({admin.email})")
            
            # Check if the admin has a profile
            admin_profile = Admin.query.filter_by(user_id=admin.id).first()
            if admin_profile:
                print(f"  Profile: {admin_profile.full_name}")
            else:
                print("  No profile found")
        
        # Create a new admin user with a simple username and password
        admin_email = "admin@example.com"
        admin_username = "admin"
        admin_password = "admin123"
        
        # Check if this admin already exists
        existing_user = User.query.filter_by(email=admin_email).first()
        if existing_user:
            print(f"\nAdmin user with email {admin_email} already exists.")
            
            # Update the password to make sure it's correct
            hashed_password = bcrypt.generate_password_hash(admin_password).decode('utf-8')
            existing_user.password = hashed_password
            db.session.commit()
            
            print(f"Password updated for {admin_username}.")
            print(f"You can now log in with:")
            print(f"Email: {admin_email}")
            print(f"Password: {admin_password}")
            print(f"Make sure to select 'Admin' as the role when logging in.")
        else:
            print(f"\nCreating new admin user...")
            
            # Create user
            hashed_password = bcrypt.generate_password_hash(admin_password).decode('utf-8')
            user = User(
                username=admin_username,
                email=admin_email,
                password=hashed_password,
                role='admin'
            )
            
            db.session.add(user)
            db.session.commit()
            
            # Get the first school
            from app.models import School
            school = School.query.first()
            
            if school:
                # Create admin profile
                admin = Admin(
                    user_id=user.id,
                    full_name="System Administrator",
                    school_id=school.id
                )
                
                db.session.add(admin)
                db.session.commit()
                
                print(f"Admin user created successfully!")
                print(f"You can now log in with:")
                print(f"Email: {admin_email}")
                print(f"Password: {admin_password}")
                print(f"Make sure to select 'Admin' as the role when logging in.")
            else:
                print("No school found. Admin profile not created.")

if __name__ == "__main__":
    fix_login() 