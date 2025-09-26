"""
Authentication Routes for Mina User Management
Handles registration, login, logout, and user management functionality.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from models import db, User, Workspace
import re


auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


def is_valid_email(email):
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def is_valid_password(password):
    """Validate password strength."""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r'[A-Za-z]', password):
        return False, "Password must contain at least one letter"
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one number"
    return True, "Valid password"


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration page and handler."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        # Get form data
        email = request.form.get('email', '').strip().lower()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        
        # Validation
        errors = []
        
        if not email:
            errors.append("Email is required")
        elif not is_valid_email(email):
            errors.append("Please enter a valid email address")
        elif User.query.filter_by(email=email).first():
            errors.append("An account with this email already exists")
        
        if not username:
            errors.append("Username is required")
        elif len(username) < 3:
            errors.append("Username must be at least 3 characters long")
        elif User.query.filter_by(username=username).first():
            errors.append("This username is already taken")
        
        if not password:
            errors.append("Password is required")
        else:
            valid, message = is_valid_password(password)
            if not valid:
                errors.append(message)
        
        if password != confirm_password:
            errors.append("Passwords do not match")
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('auth/register.html')
        
        try:
            # Create new user
            user = User(
                email=email,
                username=username,
                first_name=first_name,
                last_name=last_name
            )
            user.set_password(password)
            
            # For first user, create personal workspace
            if User.query.count() == 0:
                user.role = 'owner'
            
            db.session.add(user)
            db.session.commit()
            
            # Create personal workspace for new user
            workspace_name = f"{first_name}'s Workspace" if first_name else f"{username}'s Workspace"
            workspace = Workspace(
                name=workspace_name,
                slug=Workspace.generate_slug(workspace_name),
                owner_id=user.id
            )
            db.session.add(workspace)
            
            # Assign user to workspace
            user.workspace_id = workspace.id
            db.session.commit()
            
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db.session.rollback()
            flash('Registration failed. Please try again.', 'error')
            return render_template('auth/register.html')
    
    return render_template('auth/register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login page and handler."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        email_or_username = request.form.get('email_or_username', '').strip()
        password = request.form.get('password', '')
        remember_me = request.form.get('remember_me') == 'on'
        
        if not email_or_username or not password:
            flash('Please enter both email/username and password', 'error')
            return render_template('auth/login.html')
        
        # Find user by email or username
        user = None
        if '@' in email_or_username:
            user = User.query.filter_by(email=email_or_username.lower()).first()
        else:
            user = User.query.filter_by(username=email_or_username).first()
        
        if user and user.check_password(password):
            if not user.active:
                flash('Your account has been deactivated. Please contact support.', 'error')
                return render_template('auth/login.html')
            
            # Log in user
            login_user(user, remember=remember_me)
            user.update_last_login()
            db.session.commit()
            
            # Redirect to next page or dashboard
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            return redirect(url_for('dashboard.index'))
        else:
            flash('Invalid email/username or password', 'error')
    
    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """User logout handler."""
    logout_user()
    flash('You have been logged out successfully', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/profile')
@login_required
def profile():
    """User profile page."""
    return render_template('auth/profile.html', user=current_user)


@auth_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Edit user profile."""
    if request.method == 'POST':
        # Get form data
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        display_name = request.form.get('display_name', '').strip()
        timezone = request.form.get('timezone', 'UTC')
        
        try:
            # Update user profile
            current_user.first_name = first_name
            current_user.last_name = last_name
            current_user.display_name = display_name
            current_user.timezone = timezone
            
            db.session.commit()
            flash('Profile updated successfully', 'success')
            return redirect(url_for('auth.profile'))
            
        except Exception as e:
            db.session.rollback()
            flash('Failed to update profile. Please try again.', 'error')
    
    return render_template('auth/edit_profile.html', user=current_user)


@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change user password."""
    if request.method == 'POST':
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validation
        if not current_user.check_password(current_password):
            flash('Current password is incorrect', 'error')
            return render_template('auth/change_password.html')
        
        valid, message = is_valid_password(new_password)
        if not valid:
            flash(message, 'error')
            return render_template('auth/change_password.html')
        
        if new_password != confirm_password:
            flash('New passwords do not match', 'error')
            return render_template('auth/change_password.html')
        
        try:
            current_user.set_password(new_password)
            db.session.commit()
            flash('Password changed successfully', 'success')
            return redirect(url_for('auth.profile'))
            
        except Exception as e:
            db.session.rollback()
            flash('Failed to change password. Please try again.', 'error')
    
    return render_template('auth/change_password.html')


@auth_bp.route('/api/user')
@login_required
def api_user():
    """API endpoint to get current user data."""
    return jsonify(current_user.to_dict())


@auth_bp.route('/api/check-username')
def api_check_username():
    """API endpoint to check if username is available."""
    username = request.args.get('username', '').strip()
    if not username:
        return jsonify({'available': False, 'message': 'Username is required'})
    
    if len(username) < 3:
        return jsonify({'available': False, 'message': 'Username must be at least 3 characters'})
    
    user = User.query.filter_by(username=username).first()
    if user:
        return jsonify({'available': False, 'message': 'Username is already taken'})
    
    return jsonify({'available': True, 'message': 'Username is available'})


@auth_bp.route('/api/check-email')
def api_check_email():
    """API endpoint to check if email is available."""
    email = request.args.get('email', '').strip().lower()
    if not email:
        return jsonify({'available': False, 'message': 'Email is required'})
    
    if not is_valid_email(email):
        return jsonify({'available': False, 'message': 'Invalid email format'})
    
    user = User.query.filter_by(email=email).first()
    if user:
        return jsonify({'available': False, 'message': 'Email is already registered'})
    
    return jsonify({'available': True, 'message': 'Email is available'})