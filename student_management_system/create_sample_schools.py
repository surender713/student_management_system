from app import create_app, db, bcrypt
from app.models import School, MasterAdmin, User, Admin

def create_sample_data():
    app = create_app()
    
    with app.app_context():
        # Create master admin if not exists
        if not MasterAdmin.query.first():
            hashed_password = bcrypt.generate_password_hash('master123').decode('utf-8')
            master_admin = MasterAdmin(
                username='masteradmin',
                email='master@example.com',
                password=hashed_password,
                full_name='Master Administrator'
            )
            
            db.session.add(master_admin)
            db.session.commit()
            print("Master admin created successfully!")
        else:
            print("Master admin already exists.")
        
        # Create sample schools
        schools_data = [
            {
                'name': 'ABC Public School',
                'school_number': 'ABC123',
                'password': 'school123',
                'address': '123 Main Street, City',
                'phone': '123-456-7890',
                'email': 'info@abcschool.com',
                'website': 'www.abcschool.com'
            },
            {
                'name': 'XYZ International School',
                'school_number': 'XYZ456',
                'password': 'school123',
                'address': '456 Park Avenue, City',
                'phone': '987-654-3210',
                'email': 'info@xyzschool.com',
                'website': 'www.xyzschool.com'
            },
            {
                'name': 'PQR Academy',
                'school_number': 'PQR789',
                'password': 'school123',
                'address': '789 College Road, City',
                'phone': '567-890-1234',
                'email': 'info@pqracademy.com',
                'website': 'www.pqracademy.com'
            }
        ]
        
        for school_data in schools_data:
            if not School.query.filter_by(school_number=school_data['school_number']).first():
                hashed_password = bcrypt.generate_password_hash(school_data['password']).decode('utf-8')
                school = School(
                    name=school_data['name'],
                    school_number=school_data['school_number'],
                    password=hashed_password,
                    address=school_data['address'],
                    phone=school_data['phone'],
                    email=school_data['email'],
                    website=school_data['website']
                )
                
                db.session.add(school)
                db.session.commit()
                
                # Create a school admin for each school
                admin_username = f"admin_{school_data['school_number'].lower()}"
                admin_email = f"admin@{school_data['website'].replace('www.', '')}"
                
                if not User.query.filter_by(username=admin_username).first():
                    hashed_password = bcrypt.generate_password_hash('admin123').decode('utf-8')
                    user = User(
                        username=admin_username,
                        email=admin_email,
                        password=hashed_password,
                        role='admin'
                    )
                    
                    db.session.add(user)
                    db.session.commit()
                    
                    admin = Admin(
                        user_id=user.id,
                        full_name=f"Admin {school.name}",
                        phone=school.phone,
                        school_id=school.id
                    )
                    
                    db.session.add(admin)
                    db.session.commit()
                
                print(f"School '{school_data['name']}' created with admin!")
            else:
                print(f"School '{school_data['name']}' already exists.")
        
        print("Sample data creation completed!")

if __name__ == '__main__':
    create_sample_data()