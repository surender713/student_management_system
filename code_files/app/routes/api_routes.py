from flask import Blueprint, jsonify
from app.models import Subject, Class
from flask_login import login_required

# Create blueprint
api = Blueprint('api', __name__)

@api.route('/classes/<int:class_id>/subjects', methods=['GET'])
@login_required
def get_subjects_for_class(class_id):
    """Get all subjects for a specific class"""
    subjects = Subject.query.filter_by(class_id=class_id).all()
    
    subjects_data = [
        {
            'id': subject.id,
            'name': subject.name,
            'code': subject.code
        }
        for subject in subjects
    ]
    
    return jsonify({
        'success': True,
        'subjects': subjects_data
    }) 