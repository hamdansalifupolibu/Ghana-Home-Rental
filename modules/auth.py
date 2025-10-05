from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from modules.database import get_db_connection
from werkzeug.security import generate_password_hash, check_password_hash
import re

auth_bp = Blueprint('auth', __name__)

# Helper function to validate email
def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        full_name = request.form['full_name']
        phone = request.form['phone']
        role = request.form['role']

        # Validation
        if not all([username, email, password, confirm_password, full_name]):
            flash('All fields are required!', 'error')
            return render_template('auth/register.html')

        if not is_valid_email(email):
            flash('Please enter a valid email address!', 'error')
            return render_template('auth/register.html')

        if password != confirm_password:
            flash('Passwords do not match!', 'error')
            return render_template('auth/register.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters long!', 'error')
            return render_template('auth/register.html')

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            # Check if username or email already exists
            cursor.execute("SELECT * FROM users WHERE username = %s OR email = %s", (username, email))
            existing_user = cursor.fetchone()

            if existing_user:
                if existing_user['username'] == username:
                    flash('Username already exists!', 'error')
                else:
                    flash('Email already registered!', 'error')
                return render_template('auth/register.html')

            # Hash password and create user
            hashed_password = generate_password_hash(password)

            cursor.execute("""
                INSERT INTO users (username, email, password_hash, full_name, phone, role)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (username, email, hashed_password, full_name, phone, role))

            conn.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('auth.login'))

        except Exception as e:
            conn.rollback()
            flash(f'Registration failed: {str(e)}', 'error')
        finally:
            cursor.close()
            conn.close()

    return render_template('auth/register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user_type = request.form.get('user_type', 'tenant')  # tenant, landlord, admin

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            # Find user by username or email
            cursor.execute("SELECT * FROM users WHERE username = %s OR email = %s", (username, username))
            user = cursor.fetchone()

            if user and check_password_hash(user['password_hash'], password):
                # Check if user role matches the selected user_type
                if user_type == 'admin' and user['role'] != 'admin':
                    flash('Admin access denied!', 'error')
                elif user_type == 'landlord' and user['role'] not in ['landlord', 'admin']:
                    flash('Landlord access denied!', 'error')
                else:
                    # Successful login
                    session['user_id'] = user['id']
                    session['username'] = user['username']
                    session['role'] = user['role']
                    session['logged_in'] = True

                    flash(f'Welcome back, {user["full_name"]}!', 'success')

                    # SAFE REDIRECTS - Check which routes actually exist
                    if user['role'] == 'admin':
                        # Try admin dashboard, fallback to home if not exists
                        try:
                            return redirect(url_for('admin.dashboard'))
                        except:
                            return redirect(url_for('user.index'))
                    elif user['role'] == 'landlord':
                        # Try landlord dashboard, fallback to home if not exists
                        try:
                            return redirect(url_for('admin.landlord_dashboard'))
                        except:
                            return redirect(url_for('user.index'))
                    else:
                        # Try tenant dashboard, fallback to home if not exists
                        try:
                            return redirect(url_for('user.tenant_dashboard'))
                        except:
                            return redirect(url_for('user.index'))
            else:
                flash('Invalid username or password!', 'error')

        except Exception as e:
            flash(f'Login error: {str(e)}', 'error')
        finally:
            cursor.close()
            conn.close()

    return render_template('auth/login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('user.index'))

# Profile page - UPDATED WITH SAFE REDIRECTS
@auth_bp.route('/profile')
def profile():
    if not session.get('logged_in'):
        flash('Please login to view your profile.', 'error')
        return redirect(url_for('auth.login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("SELECT * FROM users WHERE id = %s", (session['user_id'],))
        user = cursor.fetchone()
    except Exception as e:
        flash(f'Error loading profile: {str(e)}', 'error')
        return redirect(url_for('user.index'))
    finally:
        cursor.close()
        conn.close()

    return render_template('auth/profile.html', user=user)

@auth_bp.route('/profile/edit', methods=['GET', 'POST'])
def edit_profile():
    if not session.get('logged_in'):
        flash('Please login to edit your profile.', 'error')
        return redirect(url_for('auth.login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        try:
            # Get form data
            email = request.form['email']
            full_name = request.form['full_name']
            phone = request.form['phone']
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')

            # Basic validation
            if not email or not full_name:
                flash('Email and Full Name are required!', 'error')
                return redirect(url_for('auth.edit_profile'))

            if not is_valid_email(email):
                flash('Please enter a valid email address!', 'error')
                return redirect(url_for('auth.edit_profile'))

            # Check if email is already taken by another user
            cursor.execute("SELECT id FROM users WHERE email = %s AND id != %s",
                           (email, session['user_id']))
            if cursor.fetchone():
                flash('Email already registered by another user!', 'error')
                return redirect(url_for('auth.edit_profile'))

            # Update query base
            update_query = "UPDATE users SET email = %s, full_name = %s, phone = %s"
            params = [email, full_name, phone]

            # Handle password change if provided
            if current_password and new_password:
                # Verify current password
                cursor.execute("SELECT password_hash FROM users WHERE id = %s", (session['user_id'],))
                user = cursor.fetchone()

                if not check_password_hash(user['password_hash'], current_password):
                    flash('Current password is incorrect!', 'error')
                    return redirect(url_for('auth.edit_profile'))

                if new_password != confirm_password:
                    flash('New passwords do not match!', 'error')
                    return redirect(url_for('auth.edit_profile'))

                if len(new_password) < 6:
                    flash('New password must be at least 6 characters long!', 'error')
                    return redirect(url_for('auth.edit_profile'))

                # Add password to update
                update_query += ", password_hash = %s"
                params.append(generate_password_hash(new_password))

            # Complete the update query
            update_query += " WHERE id = %s"
            params.append(session['user_id'])

            # Execute update
            cursor.execute(update_query, params)
            conn.commit()

            # Update session data
            session['username'] = email.split('@')[0]  # Update username from email

            flash('Profile updated successfully!', 'success')
            return redirect(url_for('auth.profile'))

        except Exception as e:
            conn.rollback()
            flash(f'Error updating profile: {str(e)}', 'error')
        finally:
            cursor.close()
            conn.close()

    else:
        # GET request - load current user data
        try:
            cursor.execute("SELECT * FROM users WHERE id = %s", (session['user_id'],))
            user = cursor.fetchone()
        except Exception as e:
            flash(f'Error loading profile: {str(e)}', 'error')
            return redirect(url_for('user.index'))
        finally:
            cursor.close()
            conn.close()

    return render_template('auth/edit_profile.html', user=user)
