import sys
import os
from flask import Flask
from app import create_app, db, bcrypt
from app.models import MasterAdmin

# Create the Flask application
app = create_app()

def create_master_admin():
    with app.app_context():
        # Check if there are any master admins
        existing_master = MasterAdmin.query.filter_by(username="admin1").first()
        
        if existing_master:
            print("Master admin already exists with username 'admin1'")
            return
        
        # Create a new master admin
        hashed_password = bcrypt.generate_password_hash("password").decode('utf-8')
        master_admin = MasterAdmin(
            username="admin1",
            email="masteradmin@example.com",
            password=hashed_password,
            full_name="Master Admin"
        )
        
        db.session.add(master_admin)
        db.session.commit()
        
        print("Master admin created successfully!")
        print("You can now log in with the following credentials:")
        print("Username: admin1")
        print("Password: password")

if __name__ == "__main__":
    create_master_admin() 