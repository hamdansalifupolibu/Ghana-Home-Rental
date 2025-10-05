from flask import Blueprint, render_template, request, session, flash, redirect, url_for
import json
from modules.database import get_db_connection

user_bp = Blueprint('user', __name__)

@user_bp.route('/')
def index():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Get featured houses (limit to 6 for homepage)
    cursor.execute("""
        SELECT h.*, r.name as region_name, n.name as neighborhood_name
        FROM houses h
        LEFT JOIN regions r ON h.region_id = r.id
        LEFT JOIN neighborhoods n ON h.neighborhood_id = n.id
        ORDER BY h.created_at DESC
        LIMIT 6
    """)
    featured_houses = cursor.fetchall()

    # FIX: Properly parse image_paths for each house
    for house in featured_houses:
        if house['image_paths']:
            try:
                # If it's a string, parse it as JSON/list
                if isinstance(house['image_paths'], str):
                    house['image_paths'] = json.loads(house['image_paths'].replace("'", '"'))
            except:
                # If parsing fails, set to empty list
                house['image_paths'] = []
        else:
            # If NULL or empty, set to empty list
            house['image_paths'] = []

    # Get all regions for filter
    cursor.execute("SELECT * FROM regions")
    regions = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('user/index.html',
                           featured_houses=featured_houses,
                           regions=regions)

@user_bp.route('/houses')
def houses():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Get filter parameters
    region_filter = request.args.get('region', '')
    property_type_filter = request.args.get('property_type', '')
    min_price = request.args.get('min_price', '')
    max_price = request.args.get('max_price', '')

    # Build query with filters
    query = """
        SELECT h.*, r.name as region_name, n.name as neighborhood_name
        FROM houses h
        LEFT JOIN regions r ON h.region_id = r.id
        LEFT JOIN neighborhoods n ON h.neighborhood_id = n.id
        WHERE 1=1
    """
    params = []

    if region_filter:
        query += " AND h.region_id = %s"
        params.append(region_filter)

    if property_type_filter:
        query += " AND h.property_type = %s"
        params.append(property_type_filter)

    if min_price:
        query += " AND h.price >= %s"
        params.append(min_price)

    if max_price:
        query += " AND h.price <= %s"
        params.append(max_price)

    query += " ORDER BY h.created_at DESC"

    cursor.execute(query, params)
    houses = cursor.fetchall()

    # FIX: Apply the same image parsing to houses page
    for house in houses:
        if house['image_paths']:
            try:
                # If it's a string, parse it as JSON/list
                if isinstance(house['image_paths'], str):
                    house['image_paths'] = json.loads(house['image_paths'].replace("'", '"'))
            except:
                # If parsing fails, set to empty list
                house['image_paths'] = []
        else:
            # If NULL or empty, set to empty list
            house['image_paths'] = []

    # Get all regions for filter dropdown
    cursor.execute("SELECT * FROM regions")
    regions = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('user/houses.html',
                           houses=houses,
                           regions=regions,
                           current_region=region_filter,
                           current_property_type=property_type_filter,
                           current_min_price=min_price,
                           current_max_price=max_price)

@user_bp.route('/house/<int:house_id>')
def house_detail(house_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Get house details
    cursor.execute("""
        SELECT h.*, r.name as region_name, n.name as neighborhood_name
        FROM houses h
        LEFT JOIN regions r ON h.region_id = r.id
        LEFT JOIN neighborhoods n ON h.neighborhood_id = n.id
        WHERE h.id = %s
    """, (house_id,))
    house = cursor.fetchone()

    if not house:
        cursor.close()
        conn.close()
        return "House not found", 404

    # FIX: Apply the same image parsing to house detail page
    if house['image_paths']:
        try:
            # If it's a string, parse it as JSON/list
            if isinstance(house['image_paths'], str):
                house['image_paths'] = json.loads(house['image_paths'].replace("'", '"'))
        except:
            # If parsing fails, set to empty list
            house['image_paths'] = []
    else:
        # If NULL or empty, set to empty list
        house['image_paths'] = []

    cursor.close()
    conn.close()

    return render_template('user/house_detail.html', house=house)

@user_bp.route('/tenant-dashboard')
def tenant_dashboard():
    if not session.get('logged_in'):
        flash('Please login to access your dashboard.', 'error')
        return redirect(url_for('auth.login'))
    return render_template('user/tenant_dashboard.html')

