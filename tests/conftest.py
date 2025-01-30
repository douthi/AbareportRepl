import os
import pytest
from app import app as flask_app, db

@pytest.fixture
def app():
    """Create application for the tests."""
    flask_app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': os.environ.get('DATABASE_URL'),
        'SQLALCHEMY_ENGINE_OPTIONS': {
            'pool_recycle': 300,
            'pool_pre_ping': True,
        },
        'WTF_CSRF_ENABLED': False  # Disable CSRF for testing
    })

    with flask_app.app_context():
        # Create tables for testing
        db.create_all()
        yield flask_app  # Return the app for tests to use
        # Clean up after tests
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """Create a test client for the app."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """Create a test CLI runner for the app."""
    return app.test_cli_runner()