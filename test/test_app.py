import os
import sys
import pytest

# Add parent directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from myapp import app, db
from models import User
import json

@pytest.fixture
def client():
    """Configure Flask test client with a test database."""
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False

    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.session.remove()
            db.drop_all()

@pytest.fixture
def sample_user(client):
    """Create a sample user for testing."""
    user = User(
        name='Test User',
        email='test@example.com',
        password='testpass',
        mobile_number='1234567890'
    )
    db.session.add(user)
    db.session.commit()
    return user

# Web Interface Tests
def test_index_redirect(client):
    """Test that root URL redirects to users list."""
    response = client.get('/')
    assert response.status_code == 302
    assert '/web/users' in response.location

def test_list_users_empty(client):
    """Test users list when no users exist."""
    response = client.get('/web/users')
    assert response.status_code == 200
    assert b'Users List' in response.data
    assert b'Test User' not in response.data

def test_list_users_with_data(client, sample_user):
    """Test users list with existing user."""
    response = client.get('/web/users')
    assert response.status_code == 200
    assert b'Test User' in response.data
    assert b'test@example.com' in response.data

def test_create_user_form_get(client):
    """Test get request to user creation form."""
    response = client.get('/web/users/create')
    assert response.status_code == 200
    # Check for form elements instead of template name
    assert b'<form' in response.data
    assert b'name="name"' in response.data
    assert b'name="email"' in response.data

def test_create_user_form_post_success(client):
    """Test successful user creation through web interface."""
    response = client.post('/web/users/create', data={
        'name': 'New User',
        'email': 'new@example.com',
        'pwd': 'newpass',
        'mobile': '9876543210'
    })
    assert response.status_code == 302
    assert '/web/users' in response.location
    
    # Verify user was created
    user = User.query.filter_by(email='new@example.com').first()
    assert user is not None
    assert user.name == 'New User'

def test_create_user_form_post_invalid(client):
    """Test user creation with invalid data."""
    response = client.post('/web/users/create', data={})
    assert response.status_code == 200
    assert b'Error' in response.data

def test_edit_user_form_get(client, sample_user):
    """Test get request to user edit form."""
    response = client.get(f'/web/users/{sample_user.id}/edit')
    assert response.status_code == 200
    assert b'Test User' in response.data

def test_edit_user_form_get_nonexistent(client):
    """Test get request to edit non-existent user."""
    response = client.get('/web/users/999/edit', follow_redirects=True)
    assert b'User not found' in response.data

def test_edit_user_form_post_success(client, sample_user):
    """Test successful user update through web interface."""
    response = client.post(f'/web/users/{sample_user.id}/edit', data={
        'name': 'Updated Name',
        'email': 'updated@example.com',
        'mobile': '5555555555',
        'pwd': 'newpass'
    })
    assert response.status_code == 302
    
    # Verify user was updated
    user = User.query.get(sample_user.id)
    assert user.name == 'Updated Name'
    assert user.email == 'updated@example.com'

def test_delete_user_web_success(client, sample_user):
    """Test successful user deletion through web interface."""
    response = client.post(f'/web/users/{sample_user.id}/delete')
    assert response.status_code == 302
    
    # Verify user was deleted
    user = User.query.get(sample_user.id)
    assert user is None

def test_delete_user_web_nonexistent(client):
    """Test deletion of non-existent user."""
    response = client.post('/web/users/999/delete', follow_redirects=True)
    assert b'Error' in response.data

# API Tests
def test_get_all_users_api_empty(client):
    """Test API endpoint for getting all users when empty."""
    response = client.get('/user')
    data = json.loads(response.data)
    assert response.status_code == 200
    assert data['status'] == 200
    assert len(data['data']) == 0

def test_get_all_users_api_with_data(client, sample_user):
    """Test API endpoint for getting all users with data."""
    response = client.get('/user')
    data = json.loads(response.data)
    assert response.status_code == 200
    assert data['status'] == 200
    assert len(data['data']) == 1
    assert data['data'][0][1] == 'Test User'

def test_get_specific_user_api_success(client, sample_user):
    """Test API endpoint for getting specific user."""
    response = client.get(f'/user/{sample_user.id}')
    data = json.loads(response.data)
    assert response.status_code == 200
    assert data['status'] == 200
    assert data['data'][0][1] == 'Test User'

def test_get_specific_user_api_nonexistent(client):
    """Test API endpoint for getting non-existent user."""
    response = client.get('/user/999')
    data = json.loads(response.data)
    assert response.status_code == 200
    assert data['status'] == 404
    assert 'User not exists' in data['message']

def test_create_user_api_success(client):
    """Test API endpoint for creating user."""
    response = client.post('/user', data={
        'name': 'API User',
        'email': 'api@example.com',
        'pwd': 'apipass',
        'mobile': '1231231234'
    })
    data = json.loads(response.data)
    assert response.status_code == 200
    assert data['status'] == 201
    assert 'user_id' in data

def test_create_user_api_invalid(client):
    """Test API endpoint for creating user with invalid data."""
    response = client.post('/user', data={})
    data = json.loads(response.data)
    assert response.status_code == 200
    # API creates user with empty strings for missing fields
    assert data['status'] == 201
    assert 'user_id' in data

def test_update_user_api_success(client, sample_user):
    """Test API endpoint for updating user."""
    response = client.put(f'/user/{sample_user.id}', data={
        'name': 'Updated API User',
        'email': 'updated_api@example.com'
    })
    data = json.loads(response.data)
    assert response.status_code == 200
    assert data['status'] == 200
    
    # Verify update
    user = User.query.get(sample_user.id)
    assert user.name == 'Updated API User'
    assert user.email == 'updated_api@example.com'

def test_update_user_api_nonexistent(client):
    """Test API endpoint for updating non-existent user."""
    response = client.put('/user/999', data={
        'name': 'Updated Name'
    })
    data = json.loads(response.data)
    assert response.status_code == 200
    assert data['status'] == 404

def test_delete_user_api_success(client, sample_user):
    """Test API endpoint for deleting user."""
    response = client.delete(f'/user/{sample_user.id}')
    data = json.loads(response.data)
    assert response.status_code == 200
    assert data['status'] == 200
    
    # Verify deletion
    user = User.query.get(sample_user.id)
    assert user is None

def test_delete_user_api_nonexistent(client):
    """Test API endpoint for deleting non-existent user."""
    response = client.delete('/user/999')
    data = json.loads(response.data)
    assert response.status_code == 200
    assert data['status'] == 404