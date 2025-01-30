"""
Routes package for the CRM Sync application.
Contains all route blueprints for different parts of the application.
"""
from flask import Blueprint

# Initialize blueprints
pipedrive_config = Blueprint('pipedrive_config', __name__, url_prefix='/pipedrive')
