from app import create_app, db, bcrypt
from app.models import User

app = create_app()

def check_auth():
    with app.app_context():
        # Try to authenticate admin1
        email = "admin1@example.com"
        password = "password"
        
        user = User.query.filter_by(email=email).first()
        
        if not user:
            print(f"No user found with email: {email}")
            return
        
        print(f"Found user: {user.username}, Role: {user.role}")
        print(f"Stored password hash: {user.password}")
        
        # Check if password matches
        is_valid = bcrypt.check_password_hash(user.password, password)
        print(f"Password valid: {is_valid}")
        
        # Create a new hash for comparison
        new_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        print(f"New hash for same password: {new_hash}")
        
        # Check if the new hash is valid for the same password
        is_new_valid = bcrypt.check_password_hash(new_hash, password)
        print(f"New hash valid: {is_new_valid}")

if __name__ == "__main__":
    check_auth() 