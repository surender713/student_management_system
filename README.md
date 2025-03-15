# Student Management System

A comprehensive web application for managing student data, performance tracking, and academic analytics.

## Features

### Admin Features
- Full Control Dashboard — Manage all students, teachers, and performance data
- Add New Students & Teachers — Easily register new users with roles
- Class-Wise Rankings — View and compare top-performing students per class
- Subject-Wise Performance Analysis — Dive into student performance per subject
- Top Students Overview — Identify the highest achievers across subjects and classes
- Data Export — Export student records to CSV for offline records

### Teacher Features
- Class Performance Dashboard — View class-specific performance and rankings
- Subject Analytics — Track student progress subject-by-subject
- Student Profiles — Access individual student data for better mentoring

### Student Features
- Personal Dashboard — Track their academic progress at a glance
- Class Ranking Display — See their rank among classmates
- Subject-Wise Analysis — Visual breakdown of performance in each subject
- Performance Trend Graphs — Graphs showing progress over time
- Top Student Insights — See what the top students are doing differently
- Goal Setting — Students can set academic goals and track progress

## Tech Stack
- Backend: Flask (Python)
- Database: MySQL
- Frontend: HTML, CSS, JavaScript

## Installation

1. Clone the repository:
```
git clone https://github.com/yourusername/student_management_system.git
cd student_management_system
```

2. Create a virtual environment and activate it:
```
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the required packages:
```
pip install -r requirements.txt
```

4. Set up the MySQL database:
- Create a database named `student_management`
- Update the database configuration in `app/config.py`

5. Initialize the database:
```
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

6. Run the application:
```
python run.py
```

7. Access the application at `http://localhost:5000`

## Project Structure
```
/student_management_system
│
├── /app
│   ├── __init__.py          # Initialize the Flask app
│   ├── routes.py            # Define routes and views
│   ├── models.py            # Define database models
│   ├── utils.py             # Utility functions (e.g., hashing, analytics)
│   └── config.py            # Configuration settings (database, secret key)
│
├── /static
│   ├── /css
│   └── /js
│
├── /templates
│   ├── layout.html
│   ├── login.html
│   ├── dashboard.html
│   ├── add_student.html
│   ├── view_student.html
│   ├── top_students.html
│   └── class_ranking.html
│
├── requirements.txt         # Python dependencies
├── run.py                   # Entry point to start the app
└── README.md                # Project documentation
```

## License
This project is licensed under the MIT License - see the LICENSE file for details. 
