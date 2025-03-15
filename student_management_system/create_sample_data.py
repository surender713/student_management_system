import os
import sys
import datetime
from flask import Flask
from app import create_app, db, bcrypt
from app.models import User, Admin, Teacher, Student, Class, School

# Create the Flask application
app = create_app()

def create_sample_data(force=False):
    with app.app_context():
        # Check if data already exists
        if School.query.count() > 0 and not force:
            print("Data already exists in the database. Use --force to override.")
            return
        
        # If force is True, delete existing data
        if force:
            print("Deleting existing data...")
            # Delete in reverse order of dependencies
            db.session.query(Student).delete()
            db.session.query(Class).delete()
            db.session.query(Teacher).delete()
            db.session.query(Admin).delete()
            db.session.query(User).delete()
            db.session.query(School).delete()
            db.session.commit()
            print("Existing data deleted.")
        
        # Create 5 schools
        schools = []
        for i in range(1, 6):
            school = School(
                name=f"School {i}",
                address=f"Address for School {i}",
                phone=f"123-456-{7890+i}",
                email=f"school{i}@example.com",
                website=f"www.school{i}.edu",
                academic_year="2023-2024",
                term="1",
                passing_percentage=40.0
            )
            db.session.add(school)
            db.session.commit()
            schools.append(school)
            print(f"Created School: {school.name}")
        
        # Create 5 admins (one for each school)
        for i, school in enumerate(schools, 1):
            # Create user for admin
            hashed_password = bcrypt.generate_password_hash("password").decode('utf-8')
            user = User(
                username=f"admin{i}",
                email=f"admin{i}@example.com",
                password=hashed_password,
                role='admin'
            )
            db.session.add(user)
            db.session.commit()
            
            # Create admin profile
            admin = Admin(
                user_id=user.id,
                full_name=f"Admin {i}",
                phone=f"123-456-{1000+i}",
                school_id=school.id
            )
            db.session.add(admin)
            db.session.commit()
            print(f"Created Admin: {admin.full_name} for {school.name}")
        
        # Create 5 teachers for each school
        school_teachers = {}
        for school in schools:
            school_teachers[school.id] = []
            for j in range(1, 6):
                # Create user for teacher
                hashed_password = bcrypt.generate_password_hash("password").decode('utf-8')
                user = User(
                    username=f"teacher{school.id}_{j}",
                    email=f"teacher{school.id}_{j}@example.com",
                    password=hashed_password,
                    role='teacher'
                )
                db.session.add(user)
                db.session.commit()
                
                # Create teacher profile
                teacher = Teacher(
                    user_id=user.id,
                    full_name=f"Teacher {school.id}_{j}",
                    phone=f"123-456-{2000+school.id*10+j}",
                    qualification=f"Qualification {j}",
                    department=f"Department {j % 3 + 1}",
                    experience=f"{j + 5} years",
                    category=["PRT", "TGT", "PGT"][j % 3],
                    subject_specialization=["Mathematics", "Science", "English", "History", "Geography"][j % 5],
                    school_id=school.id
                )
                db.session.add(teacher)
                db.session.commit()
                school_teachers[school.id].append(teacher)
                print(f"Created Teacher: {teacher.full_name} for {school.name}")
        
        # Create a class for each school
        school_classes = {}
        for school in schools:
            # Use the first teacher as the class teacher
            class_obj = Class(
                name=f"Class {school.id}",
                section=["A", "B", "C", "D", "E"][school.id % 5],
                stream=["Science", "Commerce", "Arts"][school.id % 3] if school.id > 3 else None,
                academic_year="2023-2024",
                school_id=school.id,
                teacher_id=school_teachers[school.id][0].id
            )
            db.session.add(class_obj)
            db.session.commit()
            school_classes[school.id] = class_obj
            print(f"Created Class: {class_obj.name} - {class_obj.section} for {school.name}")
            
        # Create 5 students for each school
        for school in schools:
            for j in range(1, 6):
                # Create user for student
                hashed_password = bcrypt.generate_password_hash("password").decode('utf-8')
                user = User(
                    username=f"student{school.id}_{j}",
                    email=f"student{school.id}_{j}@example.com",
                    password=hashed_password,
                    role='student'
                )
                db.session.add(user)
                db.session.commit()
                
                # Create student profile
                student = Student(
                    user_id=user.id,
                    full_name=f"Student {school.id}_{j}",
                    roll_number=f"S{school.id}{j:02d}",
                    date_of_birth=datetime.datetime.now().date() - datetime.timedelta(days=365*15),
                    gender='male' if j % 2 == 0 else 'female',
                    address=f"Address for Student {school.id}_{j}",
                    phone=f"123-456-{3000+school.id*10+j}",
                    parent_name=f"Parent of Student {school.id}_{j}",
                    parent_phone=f"123-456-{4000+school.id*10+j}",
                    class_id=school_classes[school.id].id,
                    school_id=school.id
                )
                db.session.add(student)
                db.session.commit()
                print(f"Created Student: {student.full_name} for {school.name}")
        
        print("\nSample data creation completed successfully!")
        print("You can now log in with the following credentials:")
        print("Admin: username=admin1, password=password")
        print("Teacher: username=teacher1_1, password=password")
        print("Student: username=student1_1, password=password")

if __name__ == "__main__":
    force = "--force" in sys.argv
    create_sample_data(force) 