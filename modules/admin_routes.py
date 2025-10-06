from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from modules.database import get_db_connection
import os
import uuid
import json
from werkzeug.utils import secure_filename
from functools import wraps

admin_bp = Blueprint('admin', __name__)

# Image upload configuration
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB


def admin_required(f):
    """Decorator to require admin OR landlord role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in') or session.get('role') not in ['admin', 'landlord']:
            flash('Please login as admin or landlord to access this page.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_only(f):
    """Decorator to require admin role only"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in') or session.get('role') != 'admin':
            flash('Admin access required for this page.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def landlord_only(f):
    """Decorator to require landlord role only"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in') or session.get('role') != 'landlord':
            flash('Landlord access required for this page.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def save_uploaded_files(files, house_id):
    """Save uploaded files and return their paths"""
    uploaded_paths = []

    # Create house-specific folder
    upload_folder = 'static/uploads'
    house_folder = os.path.join(upload_folder, f'house_{house_id}')
    if not os.path.exists(house_folder):
        os.makedirs(house_folder)

    for file in files:
        if file and file.filename != '' and allowed_file(file.filename):
            # Generate unique filename
            file_ext = file.filename.rsplit('.', 1)[1].lower()
            unique_filename = f"{uuid.uuid4().hex}.{file_ext}"
            file_path = os.path.join(house_folder, unique_filename)

            # Save file
            file.save(file_path)

            # Store relative path for database
            relative_path = f"house_{house_id}/{unique_filename}"
            uploaded_paths.append(relative_path)

    return uploaded_paths


# Separate dashboard routes for admin and landlord
@admin_bp.route('/admin-dashboard')
@admin_only
def admin_dashboard():
    """Admin-only dashboard with user metrics"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Total users count
        cursor.execute("SELECT COUNT(*) as total_users FROM users")
        total_users = cursor.fetchone()['total_users']

        # Landlords count
        cursor.execute("SELECT COUNT(*) as landlords_count FROM users WHERE role = 'landlord'")
        landlords_count = cursor.fetchone()['landlords_count']

        # Tenants count
        cursor.execute("SELECT COUNT(*) as tenants_count FROM users WHERE role = 'tenant'")
        tenants_count = cursor.fetchone()['tenants_count']

        # Active vs inactive users
        cursor.execute("SELECT COUNT(*) as active_users FROM users WHERE is_active = 1")
        active_users = cursor.fetchone()['active_users']
        inactive_users = total_users - active_users

        # New signups this week
        cursor.execute("""
            SELECT COUNT(*) as weekly_signups 
            FROM users 
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        """)
        weekly_signups = cursor.fetchone()['weekly_signups']

        # New signups this month
        cursor.execute("""
            SELECT COUNT(*) as monthly_signups 
            FROM users 
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
        """)
        monthly_signups = cursor.fetchone()['monthly_signups']

        # User retention rate (simplified and more accurate)
        cursor.execute("""
            SELECT COUNT(*) as retained_users
            FROM users 
            WHERE last_login >= DATE_SUB(NOW(), INTERVAL 30 DAY)
            AND created_at <= DATE_SUB(NOW(), INTERVAL 30 DAY)
        """)
        retained_users = cursor.fetchone()['retained_users']
        
        # Users who signed up more than 30 days ago
        cursor.execute("""
            SELECT COUNT(*) as old_users 
            FROM users 
            WHERE created_at <= DATE_SUB(NOW(), INTERVAL 30 DAY)
        """)
        old_users = cursor.fetchone()['old_users']
        
        retention_rate = (retained_users / old_users * 100) if old_users > 0 else 0

        # Get total properties count for additional metrics
        cursor.execute("SELECT COUNT(*) as total_properties FROM houses")
        total_properties = cursor.fetchone()['total_properties']

        # Get featured properties count
        cursor.execute("SELECT COUNT(*) as featured_properties FROM houses WHERE is_featured = 1")
        featured_properties = cursor.fetchone()['featured_properties']

        # Get properties by type distribution
        cursor.execute("""
            SELECT property_type, COUNT(*) as count 
            FROM houses 
            GROUP BY property_type 
            ORDER BY count DESC
        """)
        property_types = cursor.fetchall()

        # Recent signups for the table
        cursor.execute("""
            SELECT username, email, role, created_at, is_active, last_login
            FROM users 
            ORDER BY created_at DESC 
            LIMIT 10
        """)
        recent_signups = cursor.fetchall()

        # Recent properties added
        cursor.execute("""
            SELECT h.title, h.created_at, u.username as created_by, r.name as region_name
            FROM houses h
            LEFT JOIN users u ON h.created_by = u.id
            LEFT JOIN regions r ON h.region_id = r.id
            ORDER BY h.created_at DESC 
            LIMIT 5
        """)
        recent_properties = cursor.fetchall()

        metrics = {
            'total_users': total_users,
            'landlords_count': landlords_count,
            'tenants_count': tenants_count,
            'active_users': active_users,
            'inactive_users': inactive_users,
            'weekly_signups': weekly_signups,
            'monthly_signups': monthly_signups,
            'retention_rate': round(retention_rate, 1),
            'total_properties': total_properties,
            'featured_properties': featured_properties,
            'property_types': property_types,
            'recent_signups': recent_signups,
            'recent_properties': recent_properties
        }

    except Exception as e:
        flash(f'Error loading metrics: {str(e)}', 'error')
        metrics = {
            'total_users': 0,
            'landlords_count': 0,
            'tenants_count': 0,
            'active_users': 0,
            'inactive_users': 0,
            'weekly_signups': 0,
            'monthly_signups': 0,
            'retention_rate': 0,
            'total_properties': 0,
            'featured_properties': 0,
            'property_types': [],
            'recent_signups': [],
            'recent_properties': []
        }
    finally:
        cursor.close()
        conn.close()

    return render_template('admin/dashboard.html', users_count=metrics['total_users'], metrics=metrics)


@admin_bp.route('/landlord-dashboard')
@landlord_only
def landlord_dashboard():
    """Landlord-only dashboard"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Get only the landlord's properties
    cursor.execute("""
        SELECT h.*, r.name as region_name, n.name as neighborhood_name
        FROM houses h
        LEFT JOIN regions r ON h.region_id = r.id
        LEFT JOIN neighborhoods n ON h.neighborhood_id = n.id
        WHERE h.created_by = %s
        ORDER BY h.created_at DESC
    """, (session['user_id'],))

    properties = cursor.fetchall()

    # Parse image_paths for each property
    for prop in properties:
        if prop['image_paths']:
            try:
                if isinstance(prop['image_paths'], str):
                    prop['image_paths'] = json.loads(prop['image_paths'].replace("'", '"'))
            except:
                prop['image_paths'] = [prop['image_paths']] if prop['image_paths'] else []
        else:
            prop['image_paths'] = []

    cursor.close()
    conn.close()

    return render_template('landlord/dashboard.html', properties=properties)


# Main dashboard route that redirects based on role
@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    """Main dashboard route - redirects based on user role"""
    if session.get('role') == 'landlord':
        return redirect(url_for('admin.landlord_dashboard'))
    else:
        return redirect(url_for('admin.admin_dashboard'))


# Admin-only house management
@admin_bp.route('/add-house', methods=['GET', 'POST'])
@admin_only
def add_house():
    """Admin-only: Add house (full access)"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Get regions and neighborhoods for dropdowns
    cursor.execute("SELECT * FROM regions")
    regions = cursor.fetchall()

    cursor.execute("SELECT * FROM neighborhoods")
    neighborhoods = cursor.fetchall()

    if request.method == 'POST':
        try:
            # Get form data
            title = request.form['title']
            description = request.form['description']
            region_id = request.form['region_id']
            neighborhood_id = request.form['neighborhood_id']
            exact_location = request.form['exact_location']
            property_type = request.form['property_type']
            completion_status = request.form['completion_status']
            months_left = request.form.get('months_left') or None
            price = request.form['price']
            is_featured = 'is_featured' in request.form

            # Get contact information
            contact_name = request.form.get('contact_name')
            contact_phone = request.form.get('contact_phone')
            contact_email = request.form.get('contact_email')

            # Insert house into database
            cursor.execute("""
                INSERT INTO houses 
                (title, description, region_id, neighborhood_id, exact_location, 
                 property_type, completion_status, months_left, price, created_by, is_featured,
                 contact_name, contact_phone, contact_email)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (title, description, region_id, neighborhood_id, exact_location,
                  property_type, completion_status, months_left, price, session['user_id'], is_featured,
                  contact_name, contact_phone, contact_email))

            house_id = cursor.lastrowid

            # Handle image uploads
            image_paths = []
            if 'images' in request.files:
                files = request.files.getlist('images')
                image_paths = save_uploaded_files(files, house_id)

            # If no images uploaded, use placeholder
            if not image_paths:
                image_paths = ['house_placeholder.jpg']

            # Update house with image paths
            cursor.execute("""
                UPDATE houses SET image_paths = %s WHERE id = %s
            """, (json.dumps(image_paths), house_id))

            conn.commit()
            flash(f'House added successfully with {len(image_paths)} images!', 'success')
            return redirect(url_for('admin.manage_houses'))

        except Exception as e:
            conn.rollback()
            flash(f'Error adding house: {str(e)}', 'error')
        finally:
            cursor.close()
            conn.close()

    else:
        cursor.close()
        conn.close()

    return render_template('admin/add_house.html',
                           regions=regions,
                           neighborhoods=neighborhoods)


# Landlord-only property management
@admin_bp.route('/landlord/add-property', methods=['GET', 'POST'])
@landlord_only
def landlord_add_property():
    """Landlord-only: Add property (restricted access)"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Get regions and neighborhoods for dropdowns
    cursor.execute("SELECT * FROM regions")
    regions = cursor.fetchall()

    cursor.execute("SELECT * FROM neighborhoods")
    neighborhoods = cursor.fetchall()

    if request.method == 'POST':
        try:
            # Get form data
            title = request.form['title']
            description = request.form['description']
            region_id = request.form['region_id']
            neighborhood_id = request.form['neighborhood_id']
            exact_location = request.form['exact_location']
            property_type = request.form['property_type']
            completion_status = request.form['completion_status']
            months_left = request.form.get('months_left') or None
            price = request.form['price']

            # Landlords cannot feature properties
            is_featured = False

            # Get contact information
            contact_name = request.form.get('contact_name')
            contact_phone = request.form.get('contact_phone')
            contact_email = request.form.get('contact_email')

            # Insert house into database
            cursor.execute("""
                INSERT INTO houses 
                (title, description, region_id, neighborhood_id, exact_location, 
                 property_type, completion_status, months_left, price, created_by, is_featured,
                 contact_name, contact_phone, contact_email)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (title, description, region_id, neighborhood_id, exact_location,
                  property_type, completion_status, months_left, price, session['user_id'], is_featured,
                  contact_name, contact_phone, contact_email))

            house_id = cursor.lastrowid

            # Handle image uploads
            image_paths = []
            if 'images' in request.files:
                files = request.files.getlist('images')
                image_paths = save_uploaded_files(files, house_id)

            # If no images uploaded, use placeholder
            if not image_paths:
                image_paths = ['house_placeholder.jpg']

            # Update house with image paths
            cursor.execute("""
                UPDATE houses SET image_paths = %s WHERE id = %s
            """, (json.dumps(image_paths), house_id))

            conn.commit()
            flash('Property added successfully!', 'success')
            return redirect(url_for('admin.landlord_dashboard'))

        except Exception as e:
            conn.rollback()
            flash(f'Error adding property: {str(e)}', 'error')
        finally:
            cursor.close()
            conn.close()

    else:
        cursor.close()
        conn.close()

    return render_template('landlord/add_property.html',
                           regions=regions,
                           neighborhoods=neighborhoods)


@admin_bp.route('/landlord/edit-property/<int:property_id>', methods=['GET', 'POST'])
@landlord_only
def landlord_edit_property(property_id):
    """Landlord-only: Edit property (only their own)"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Verify the property belongs to this landlord
    cursor.execute("SELECT * FROM houses WHERE id = %s AND created_by = %s",
                   (property_id, session['user_id']))
    property = cursor.fetchone()

    if not property:
        flash('Property not found or access denied.', 'error')
        return redirect(url_for('admin.landlord_dashboard'))

    # Get regions and neighborhoods for dropdowns
    cursor.execute("SELECT * FROM regions")
    regions = cursor.fetchall()

    cursor.execute("SELECT * FROM neighborhoods")
    neighborhoods = cursor.fetchall()

    if request.method == 'POST':
        try:
            # Get form data
            title = request.form['title']
            description = request.form['description']
            region_id = request.form['region_id']
            neighborhood_id = request.form['neighborhood_id']
            exact_location = request.form['exact_location']
            property_type = request.form['property_type']
            completion_status = request.form['completion_status']
            months_left = request.form.get('months_left') or None
            price = request.form['price']

            # Landlords cannot change featured status
            is_featured = property['is_featured']

            # Get contact information
            contact_name = request.form.get('contact_name')
            contact_phone = request.form.get('contact_phone')
            contact_email = request.form.get('contact_email')

            # Get current image paths
            current_images = []
            if property['image_paths']:
                try:
                    if isinstance(property['image_paths'], str):
                        current_images = json.loads(property['image_paths'].replace("'", '"'))
                except:
                    current_images = [property['image_paths']] if property['image_paths'] else []

            # Handle image deletions
            delete_images = request.form.getlist('delete_images')
            updated_images = [img for img in current_images if img not in delete_images]

            # Handle new image uploads
            if 'images' in request.files:
                files = request.files.getlist('images')
                new_images = save_uploaded_files(files, property_id)
                updated_images.extend(new_images)

            # If no images left, use placeholder
            if not updated_images:
                updated_images = ['house_placeholder.jpg']

            # Update property in database
            cursor.execute("""
                UPDATE houses 
                SET title = %s, description = %s, region_id = %s, neighborhood_id = %s,
                    exact_location = %s, property_type = %s, completion_status = %s,
                    months_left = %s, price = %s, is_featured = %s, 
                    image_paths = %s, updated_at = CURRENT_TIMESTAMP,
                    contact_name = %s, contact_phone = %s, contact_email = %s
                WHERE id = %s AND created_by = %s
            """, (title, description, region_id, neighborhood_id, exact_location,
                  property_type, completion_status, months_left, price, is_featured,
                  json.dumps(updated_images), contact_name, contact_phone, contact_email,
                  property_id, session['user_id']))

            conn.commit()
            flash('Property updated successfully!', 'success')
            return redirect(url_for('admin.landlord_dashboard'))

        except Exception as e:
            conn.rollback()
            flash(f'Error updating property: {str(e)}', 'error')
        finally:
            cursor.close()
            conn.close()

    else:
        # GET request - load existing property data
        try:
            # Parse image_paths if it's a string
            if property['image_paths']:
                try:
                    if isinstance(property['image_paths'], str):
                        property['image_paths'] = json.loads(property['image_paths'].replace("'", '"'))
                except:
                    property['image_paths'] = [property['image_paths']] if property['image_paths'] else []
            else:
                property['image_paths'] = []

        except Exception as e:
            flash(f'Error loading property: {str(e)}', 'error')
            return redirect(url_for('admin.landlord_dashboard'))
        finally:
            cursor.close()
            conn.close()

    return render_template('landlord/edit_property.html',
                           property=property,
                           regions=regions,
                           neighborhoods=neighborhoods)


@admin_bp.route('/landlord/delete-property/<int:property_id>', methods=['POST'])
@landlord_only
def landlord_delete_property(property_id):
    """Landlord-only: Delete property (only their own)"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Verify the property belongs to this landlord before deleting
        cursor.execute("SELECT * FROM houses WHERE id = %s AND created_by = %s",
                       (property_id, session['user_id']))
        property = cursor.fetchone()

        if not property:
            flash('Property not found or access denied.', 'error')
            return redirect(url_for('admin.landlord_dashboard'))

        # Delete house images folder if exists
        import shutil
        house_folder = f'static/uploads/house_{property_id}'
        if os.path.exists(house_folder):
            shutil.rmtree(house_folder)

        cursor.execute("DELETE FROM houses WHERE id = %s AND created_by = %s",
                       (property_id, session['user_id']))
        conn.commit()
        flash('Property deleted successfully!', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Error deleting property: {str(e)}', 'error')
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('admin.landlord_dashboard'))


# Admin-only management routes
@admin_bp.route('/manage-houses')
@admin_only
def manage_houses():
    """Admin-only: Manage all houses"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Get all houses with region and neighborhood names
    cursor.execute("""
        SELECT h.*, r.name as region_name, n.name as neighborhood_name, u.username as created_by_name
        FROM houses h
        LEFT JOIN regions r ON h.region_id = r.id
        LEFT JOIN neighborhoods n ON h.neighborhood_id = n.id
        LEFT JOIN users u ON h.created_by = u.id
        ORDER BY h.created_at DESC
    """)
    houses = cursor.fetchall()

    # Parse image_paths for each house
    for house in houses:
        if house['image_paths']:
            try:
                if isinstance(house['image_paths'], str):
                    house['image_paths'] = json.loads(house['image_paths'].replace("'", '"'))
            except:
                house['image_paths'] = [house['image_paths']] if house['image_paths'] else []
        else:
            house['image_paths'] = []

    cursor.close()
    conn.close()

    return render_template('admin/manage_houses.html', houses=houses)


@admin_bp.route('/edit-house/<int:house_id>', methods=['GET', 'POST'])
@admin_only
def edit_house(house_id):
    """Admin-only: Edit any house"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Get regions and neighborhoods for dropdowns
    cursor.execute("SELECT * FROM regions")
    regions = cursor.fetchall()

    cursor.execute("SELECT * FROM neighborhoods")
    neighborhoods = cursor.fetchall()

    if request.method == 'POST':
        try:
            # Get form data
            title = request.form['title']
            description = request.form['description']
            region_id = request.form['region_id']
            neighborhood_id = request.form['neighborhood_id']
            exact_location = request.form['exact_location']
            property_type = request.form['property_type']
            completion_status = request.form['completion_status']
            months_left = request.form.get('months_left') or None
            price = request.form['price']
            is_featured = 'is_featured' in request.form
            delete_images = request.form.getlist('delete_images')

            # Get contact information
            contact_name = request.form.get('contact_name')
            contact_phone = request.form.get('contact_phone')
            contact_email = request.form.get('contact_email')

            # Get current image paths
            cursor.execute("SELECT image_paths FROM houses WHERE id = %s", (house_id,))
            current_data = cursor.fetchone()
            current_images = []

            if current_data and current_data['image_paths']:
                try:
                    if isinstance(current_data['image_paths'], str):
                        current_images = json.loads(current_data['image_paths'].replace("'", '"'))
                except:
                    current_images = [current_data['image_paths']] if current_data['image_paths'] else []

            # Remove deleted images
            updated_images = [img for img in current_images if img not in delete_images]

            # Handle new image uploads
            if 'images' in request.files:
                files = request.files.getlist('images')
                new_images = save_uploaded_files(files, house_id)
                updated_images.extend(new_images)

            # If no images left, use placeholder
            if not updated_images:
                updated_images = ['house_placeholder.jpg']

            # Update house in database
            cursor.execute("""
                UPDATE houses 
                SET title = %s, description = %s, region_id = %s, neighborhood_id = %s,
                    exact_location = %s, property_type = %s, completion_status = %s,
                    months_left = %s, price = %s, is_featured = %s, 
                    image_paths = %s, updated_at = CURRENT_TIMESTAMP,
                    contact_name = %s, contact_phone = %s, contact_email = %s
                WHERE id = %s
            """, (title, description, region_id, neighborhood_id, exact_location,
                  property_type, completion_status, months_left, price, is_featured,
                  json.dumps(updated_images), contact_name, contact_phone, contact_email, house_id))

            conn.commit()
            flash('House updated successfully!', 'success')
            return redirect(url_for('admin.manage_houses'))

        except Exception as e:
            conn.rollback()
            flash(f'Error updating house: {str(e)}', 'error')
        finally:
            cursor.close()
            conn.close()

    else:
        # GET request - load existing house data
        try:
            cursor.execute("SELECT * FROM houses WHERE id = %s", (house_id,))
            house = cursor.fetchone()

            if not house:
                flash('House not found!', 'error')
                return redirect(url_for('admin.manage_houses'))

            # Parse image_paths if it's a string
            if house['image_paths']:
                try:
                    if isinstance(house['image_paths'], str):
                        house['image_paths'] = json.loads(house['image_paths'].replace("'", '"'))
                except:
                    house['image_paths'] = [house['image_paths']] if house['image_paths'] else []
            else:
                house['image_paths'] = []

        except Exception as e:
            flash(f'Error loading house: {str(e)}', 'error')
            return redirect(url_for('admin.manage_houses'))
        finally:
            cursor.close()
            conn.close()

    return render_template('admin/edit_house.html',
                           house=house,
                           regions=regions,
                           neighborhoods=neighborhoods)


@admin_bp.route('/delete-house/<int:house_id>', methods=['POST'])
@admin_only
def delete_house(house_id):
    """Admin-only: Delete any house"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Delete house images folder if exists
        import shutil
        house_folder = f'static/uploads/house_{house_id}'
        if os.path.exists(house_folder):
            shutil.rmtree(house_folder)

        cursor.execute("DELETE FROM houses WHERE id = %s", (house_id,))
        conn.commit()
        flash('House deleted successfully!', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Error deleting house: {str(e)}', 'error')
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('admin.manage_houses'))


@admin_bp.route('/manage-users')
@admin_only
def manage_users():
    """Admin-only: Manage users"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Get all users
    cursor.execute("SELECT * FROM users ORDER BY created_at DESC")
    users = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('admin/manage_users.html', users=users)


@admin_bp.route('/edit-user/<int:user_id>', methods=['GET', 'POST'])
@admin_only
def edit_user(user_id):
    """Admin-only: Edit users"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        try:
            # Get form data
            email = request.form['email']
            full_name = request.form['full_name']
            phone = request.form['phone']
            role = request.form['role']
            is_active = 'is_active' in request.form

            # Update user in database
            cursor.execute("""
                UPDATE users 
                SET email = %s, full_name = %s, phone = %s, role = %s, is_active = %s
                WHERE id = %s
            """, (email, full_name, phone, role, is_active, user_id))

            conn.commit()
            flash('User updated successfully!', 'success')
            return redirect(url_for('admin.manage_users'))

        except Exception as e:
            conn.rollback()
            flash(f'Error updating user: {str(e)}', 'error')
        finally:
            cursor.close()
            conn.close()

    else:
        # GET request - load user data
        try:
            cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()

            if not user:
                flash('User not found!', 'error')
                return redirect(url_for('admin.manage_users'))

        except Exception as e:
            flash(f'Error loading user: {str(e)}', 'error')
            return redirect(url_for('admin.manage_users'))
        finally:
            cursor.close()
            conn.close()

    return render_template('admin/edit_user.html', user=user)


@admin_bp.route('/delete-user/<int:user_id>', methods=['POST'])
@admin_only
def delete_user(user_id):
    """Admin-only: Delete users"""
    # Prevent admin from deleting themselves
    if user_id == session.get('user_id'):
        flash('You cannot delete your own account!', 'error')
        return redirect(url_for('admin.manage_users'))

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()
        flash('User deleted successfully!', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Error deleting user: {str(e)}', 'error')
    finally:
        cursor.close()
        conn.close()


    return redirect(url_for('admin.manage_users'))

