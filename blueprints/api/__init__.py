from flask import Blueprint

api_bp = Blueprint('api', __name__, url_prefix='/api')

from .student_api import student_api_bp
api_bp.register_blueprint(student_api_bp)
