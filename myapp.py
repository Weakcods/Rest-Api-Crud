from flask import (
    Flask, request, jsonify, render_template, redirect, url_for, flash)
from werkzeug.exceptions import NotFound
from settings import db, app
from models import User


# Web interface routes
@app.route('/')
def index():
   
    return redirect(url_for('list_users'))


@app.route('/web/users')
def list_users():
   
    try:
        users = User.query.with_entities(
            User.id, User.name,
            User.email, User.mobile_number).all()
        return render_template('users.html', users=users)
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
        return render_template('users.html', users=[])


@app.route('/web/users/create', methods=['GET', 'POST'])
def create_user_form():
    
    if request.method == 'POST':
        try:
            user = User(
                name=request.form['name'],
                email=request.form['email'],
                password=request.form['pwd'],
                mobile_number=request.form['mobile']
            )
            db.session.add(user)
            db.session.commit()
            flash('User created successfully!', 'success')
            return redirect(url_for('list_users'))
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
    return render_template('user_form.html')


@app.route('/web/users/<int:id>/edit', methods=['GET', 'POST'])
def edit_user_form(id):
    
    user = User.query.with_entities(
        User.id, User.name,
        User.email, User.mobile_number).filter_by(id=id).first()
    
    if not user:
        flash('User not found!', 'danger')
        return redirect(url_for('list_users'))
    
    if request.method == 'POST':
        try:
            current_user = User.query.get(id)
            current_user.name = request.form['name']
            current_user.email = request.form['email']
            current_user.mobile_number = request.form['mobile']
            if request.form['pwd']:
                current_user.password = request.form['pwd']
            
            db.session.commit()
            flash('User updated successfully!', 'success')
            return redirect(url_for('list_users'))
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
    
    return render_template('user_form.html', user=user)


@app.route('/web/users/<int:id>/delete', methods=['POST'])
def delete_user_web(id):
    
    try:
        user = User.query.get_or_404(id)
        db.session.delete(user)
        db.session.commit()
        flash('User deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
    return redirect(url_for('list_users'))


@app.route('/user', methods=['GET'])
def get_all_users():
    """Get all users via API."""
    try:
        users = User.query.all()
        user_list = [{
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'mobile': user.mobile_number
        } for user in users]
        
        return jsonify({
            'status': 200,
            'message': 'Users retrieved successfully',
            'data': user_list
        }), 200
    except Exception as e:
        return jsonify({
            'status': 500,
            'message': f'Error retrieving users: {str(e)}',
            'data': None
        }), 500


@app.route('/user/<int:id>', methods=['GET'])
def get_specific_user(id):
      
    message = {
      'status': 404,
      'message': 'User not exists'
    }
    data = User.query.with_entities(
      User.id, User.name,
      User.email, User.mobile_number,
      User.password).filter_by(id=id).all()
    if len(data) == 0:
        return jsonify(message)
    message.update({
      'status': 200,
      'message': 'ALl records are fetched',
      'data': data
    })
    return jsonify(message)


@app.route('/user', methods=['POST'])
def create_user():
    """Create a new user via API."""
    if not request.is_json:
        return jsonify({
            'status': 400,
            'message': 'Content-Type must be application/json',
            'data': None
        }), 400
    
    data = request.get_json()
    
    try:
        user = User(
            name=data.get('name', ''),
            email=data.get('email', ''),
            password=data.get('password', ''),
            mobile_number=data.get('mobile', '')
        )
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'status': 201,
            'message': 'User created successfully',
            'data': {
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'mobile': user.mobile_number
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 500,
            'message': f'Error creating user: {str(e)}',
            'data': None
        }), 500


@app.route('/user/<int:id>', methods=['PUT'])
def update_user(id):
    """Update an existing user via API."""
    if not request.is_json:
        return jsonify({
            'status': 400,
            'message': 'Content-Type must be application/json',
            'data': None
        }), 400

    try:
        current_user = User.query.get_or_404(id)
    except:
        return jsonify({
            'status': 404,
            'message': 'User not found',
            'data': None
        }), 404

    try:
        data = request.get_json()
        
        if 'name' in data:
            current_user.name = data['name']
        if 'email' in data:
            current_user.email = data['email']
        if 'password' in data:
            current_user.password = data['password']
        if 'mobile' in data:
            current_user.mobile_number = data['mobile']

        db.session.commit()
        
        return jsonify({
            'status': 200,
            'message': 'User updated successfully',
            'data': {
                'id': current_user.id,
                'name': current_user.name,
                'email': current_user.email,
                'mobile': current_user.mobile_number
            }
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 500,
            'message': f'Error updating user: {str(e)}',
            'data': None
        }), 500


@app.route('/user/<int:id>', methods=['DELETE'])
def delete_user(id):
    """Delete a user via API."""
    try:
        user = User.query.get_or_404(id)
        user_data = {
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'mobile': user.mobile_number
        }
        
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({
            'status': 200,
            'message': 'User deleted successfully',
            'data': user_data
        }), 200
    except Exception as e:
        db.session.rollback()
        if isinstance(e, werkzeug.exceptions.NotFound):
            return jsonify({
                'status': 404,
                'message': 'User not found',
                'data': None
            }), 404
        return jsonify({
            'status': 500,
            'message': f'Error deleting user: {str(e)}',
            'data': None
        }), 500


if __name__ == "__main__":
    db.create_all()
    app.run(host="127.0.0.1", port=5000, debug=True)