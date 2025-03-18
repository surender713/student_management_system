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
- Backend: Flask 2.3.3 (Python)
- Database: MySQL
- Frontend: HTML, CSS, JavaScript
- Data Visualization: Matplotlib 3.8.0, Seaborn 0.13.0
- Data Processing: Pandas 2.1.1

## Prerequisites
- Python 3.8 or higher
- MySQL 5.7 or higher
- pip (Python package manager)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/student_management_system.git
cd student_management_system
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the required packages:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file in the root directory with the following variables:
```env
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=your-secret-key
DATABASE_URL=mysql://username:password@localhost/student_management
```

5. Set up the MySQL database:
- Create a database named `student_management`
- Update the database configuration in `app/config.py`

6. Initialize the database:
```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

7. Run the application:
```bash
python run.py
```

8. Access the application at `http://localhost:5000`

## Development Setup

1. Install development dependencies:
```bash
pip install -r requirements-dev.txt
```

2. Set up pre-commit hooks:
```bash
pre-commit install
```

3. Run tests:
```bash
pytest
```

## Project Structure
```
/student_management_system
│
├── /app
│   ├── __init__.py          # Initialize the Flask app
│   ├── routes/              # Route handlers
│   │   ├── admin.py
│   │   ├── auth.py
│   │   ├── student.py
│   │   └── teacher.py
│   ├── models/              # Database models
│   │   ├── user.py
│   │   ├── student.py
│   │   ├── teacher.py
│   │   └── performance.py
│   ├── templates/           # HTML templates
│   ├── static/              # Static files
│   └── utils/               # Utility functions
│
├── /tests                   # Test files
├── /migrations              # Database migrations
├── .env                     # Environment variables
├── .gitignore              # Git ignore rules
├── requirements.txt         # Production dependencies
├── requirements-dev.txt     # Development dependencies
├── run.py                   # Application entry point
└── README.md               # Project documentation
```

## Contributing

1. Fork the repository
2. Create a new branch (`git checkout -b feature/improvement`)
3. Make your changes
4. Run the tests (`pytest`)
5. Commit your changes (`git commit -am 'Add new feature'`)
6. Push to the branch (`git push origin feature/improvement`)
7. Create a Pull Request

## Troubleshooting

### Common Issues

1. Database Connection Error
   - Verify MySQL is running
   - Check database credentials in `.env`
   - Ensure database exists

2. Package Installation Issues
   - Try upgrading pip: `python -m pip install --upgrade pip`
   - Clear pip cache: `pip cache purge`
   - Install packages one by one to identify problematic dependencies

3. Flask Application Not Starting
   - Check if all environment variables are set
   - Verify virtual environment is activated
   - Check for port conflicts

## License
This project is licensed under the MIT License - see the LICENSE file for details. 
