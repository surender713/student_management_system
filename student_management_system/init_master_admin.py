from app import create_app, db, bcrypt
from app.models import MasterAdmin, User

def init_master_admin():
    """Create a master admin with default credentials"""
    app = create_app()
    
    with app.app_context():
        # Check if master admin already exists
        if MasterAdmin.query.first():
            print("Master admin already exists!")
            return
        
        # Create master admin with default credentials
        username = "masteradmin"
        password = "master123"
        email = "master@admin.com"
        full_name = "Master Administrator"
        
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        master_admin = MasterAdmin(
            username=username,
            email=email,
            password=hashed_password,
            full_name=full_name
        )
        
        db.session.add(master_admin)
        db.session.commit()
        
        print(f"Master admin created successfully!")
        print(f"Username: {username}")
        print(f"Password: {password}")

if __name__ == '__main__':
    init_master_admin() 