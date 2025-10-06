from flask import Blueprint, render_template, request, session, flash, redirect, url_for, jsonify
import json
import random
import logging
from modules.database import get_db_connection

user_bp = Blueprint('user', __name__)

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







# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Property type mapping
PROPERTY_TYPE_MAPPING = {
    'single_room': ['single room', 'single', 'room', 'one room'],
    'chamber_hall': ['chamber', 'chamber hall', 'chamber and hall', 'hall'],
    '2_bedroom': ['2 bedroom', '2-bedroom', 'two bedroom', '2 bed'],
    '3_bedroom': ['3 bedroom', '3-bedroom', 'three bedroom', '3 bed'],
    'self_contained': ['self contained', 'self-contained', 'self contain', 'selfcontained'],
    'store': ['store', 'shop', 'commercial', 'business', 'retail'],
    'apartment': ['apartment', 'flat', 'unit']
}

# Region mapping
REGION_MAPPING = {
    'accra': ['accra', 'greater accra'],
    'kumasi': ['kumasi', 'ashanti'],
    'takoradi': ['takoradi', 'western'],
    'cape coast': ['cape coast', 'central'],
    'tema': ['tema'],
    'eastern': ['eastern', 'koforidua'],
    'volta': ['volta', 'ho'],
    'northern': ['northern', 'tamale']
}

def detect_property_type(user_message):
    """Detect property type from user message with fuzzy matching"""
    user_message = user_message.lower()
    
    for db_type, keywords in PROPERTY_TYPE_MAPPING.items():
        for keyword in keywords:
            if keyword in user_message:
                return db_type
    return None

def detect_region(user_message):
    """Detect region from user message"""
    user_message = user_message.lower()
    
    for region, keywords in REGION_MAPPING.items():
        for keyword in keywords:
            if keyword in user_message:
                return region
    return None

def detect_budget(user_message):
    """Extract budget range from user message"""
    user_message = user_message.lower()
    
    # Look for specific price mentions
    if 'under 1000' in user_message or 'below 1000' in user_message or 'less than 1000' in user_message:
        return 1000
    elif 'under 5000' in user_message or 'below 5000' in user_message:
        return 5000
    elif 'under 10000' in user_message or 'below 10000' in user_message:
        return 10000
    
    # Look for price numbers
    import re
    price_matches = re.findall(r'(\d+)\s*(?:ghs?|cedis?)?', user_message)
    if price_matches:
        return int(price_matches[0])
    
    return None

def get_property_type_display_name(property_type):
    """Convert database property_type to readable format"""
    return property_type.replace('_', ' ').title()

def execute_safe_query(cursor, query, params=None):
    """Execute query with proper error handling"""
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        return cursor.fetchall()
    except Exception as e:
        logger.error(f"Query failed: {e}")
        return []

@user_bp.route('/chatbot', methods=['POST'])
def chatbot():
    user_message = request.json.get('message', '').strip()
    response = ""
    properties = []
    
    if not user_message:
        return jsonify({'response': "Please type a message so I can help you! 😊", 'properties': []})
    
    logger.info(f"Chatbot received: {user_message}")
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Convert to lowercase for matching
        user_message_lower = user_message.lower()
        
        # === GREETINGS & BASIC INTERACTION ===
        if any(word in user_message_lower for word in ['hello', 'hi', 'hey', 'hola']):
            greetings = [
                "👋 Hello! I'm your GhanaRentals assistant! I can help you find properties across Ghana.",
                "🏡 Hi there! Ready to find your perfect rental? I'm here to help!",
                "😊 Hey! Welcome to GhanaRentals! What can I help you find today?"
            ]
            response = random.choice(greetings)

        # === PROPERTY SEARCH QUERIES ===
        elif any(word in user_message_lower for word in [
            'house', 'property', 'rent', 'room', 'apartment', 'looking for', 
            'need a', 'show me', 'find', 'want', 'store', 'shop', 'commercial',
            'bedroom', 'self contained', 'chamber', 'single'
        ]):
            # Detect what the user is looking for
            property_type = detect_property_type(user_message_lower)
            region = detect_region(user_message_lower)
            budget = detect_budget(user_message_lower)
            
            logger.info(f"Detected - Type: {property_type}, Region: {region}, Budget: {budget}")

            # Build query based on detected parameters
            query = """
                SELECT h.*, r.name as region_name, n.name as neighborhood_name 
                FROM houses h 
                LEFT JOIN regions r ON h.region_id = r.id 
                LEFT JOIN neighborhoods n ON h.neighborhood_id = n.id 
                WHERE 1=1
            """
            params = []
            
            # Region filter
            if region:
                if region == 'accra':
                    query += " AND r.name LIKE %s"
                    params.append('%Accra%')
                elif region == 'kumasi':
                    query += " AND r.name LIKE %s"
                    params.append('%Ashanti%')
                # Add more regions as needed
            
            # Property type filter
            if property_type:
                if property_type == 'apartment':
                    # Map 'apartment' to bedroom types
                    query += " AND h.property_type IN (%s, %s, %s)"
                    params.extend(['2_bedroom', '3_bedroom', 'self_contained'])
                else:
                    query += " AND h.property_type = %s"
                    params.append(property_type)
            
            # Budget filter
            if budget:
                query += " AND h.price <= %s"
                params.append(budget)
            
            # Order and limit
            query += " ORDER BY h.created_at DESC LIMIT 5"
            
            # Execute query
            properties = execute_safe_query(cursor, query, params)
            
            # Generate appropriate response
            if properties:
                # Build context-aware response
                response_parts = []
                
                if region:
                    response_parts.append(f"🏙️ Found in {region.title()}")
                else:
                    response_parts.append("🏠 Found")
                
                if property_type:
                    display_type = get_property_type_display_name(property_type)
                    response_parts.append(f"{display_type} properties")
                else:
                    response_parts.append("properties")
                
                if budget:
                    response_parts.append(f"under GHS {budget}")
                
                response = " ".join(response_parts) + ": "
                
                # Add property details
                for i, prop in enumerate(properties[:3]):  # Show max 3
                    prop_type_display = get_property_type_display_name(prop['property_type'])
                    response += f"{prop['title']} ({prop_type_display}) - GHS {prop['price']}. "
                
                if len(properties) > 3:
                    response += f" Plus {len(properties) - 3} more on our website!"
                    
            else:
                # No properties found - helpful suggestions
                suggestions = []
                if property_type:
                    suggestions.append(f"try different {get_property_type_display_name(property_type)} options")
                if region:
                    suggestions.append(f"try different regions besides {region}")
                if budget:
                    suggestions.append(f"adjust your budget from GHS {budget}")
                
                if suggestions:
                    response = f"🔍 No properties found. You could {', '.join(suggestions)}."
                else:
                    response = "🔍 No properties found with those criteria. Try different search terms!"

        # === AFFIRMATIVE RESPONSES ===
        elif any(word in user_message_lower for word in ['yes', 'yeah', 'sure', 'ok', 'show me', 'please']):
            # Show all available properties
            properties = execute_safe_query(cursor, """
                SELECT h.*, r.name as region_name, n.name as neighborhood_name 
                FROM houses h 
                LEFT JOIN regions r ON h.region_id = r.id 
                LEFT JOIN neighborhoods n ON h.neighborhood_id = n.id 
                ORDER BY h.created_at DESC LIMIT 6
            """)
            
            if properties:
                response = "🏡 Here are available properties: "
                for prop in properties[:4]:  # Show max 4
                    prop_type = get_property_type_display_name(prop['property_type'])
                    response += f"{prop['title']} in {prop['region_name']} ({prop_type}) - GHS {prop['price']}. "
                response += "Visit our 'Browse Houses' page for more details!"
            else:
                response = "📝 No properties listed yet. Check back soon or landlords can add properties!"

        # === HELP & GUIDANCE ===
        elif any(word in user_message_lower for word in ['help', 'what can you do', 'how does this work']):
            response = """ℹ️ I can help you:
• Find properties by type: single rooms, chamber & hall, 2/3-bedroom, self-contained, stores
• Search by location: Accra, Kumasi, Takoradi, etc.
• Filter by budget: "under GHS 1000", "budget 5000"
• Show available properties
Just tell me what you're looking for! 🏠"""

        # === CONTACT QUERIES ===
        elif any(word in user_message_lower for word in ['contact', 'landlord', 'owner', 'phone', 'email']):
            response = "📞 To contact landlords, please visit the property details page where you'll find direct contact information for quick responses!"

        # === THANK YOU ===
        elif any(word in user_message_lower for word in ['thank', 'thanks', 'appreciate']):
            responses = [
                "😊 You're very welcome! Happy to help you find your dream home!",
                "🌟 My pleasure! Don't hesitate to ask if you need more help!",
                "🏡 Anytime! Wishing you the best in your property search!"
            ]
            response = random.choice(responses)

        # === DEFAULT RESPONSE ===
        else:
            responses = [
                "🤔 I'm here to help with rental properties in Ghana. Try asking about property types, locations, or your budget!",
                "🎯 Let me help you find your perfect home! Ask me about single rooms, apartments, stores, or specific locations!",
                "🔍 I specialize in Ghana rentals! Tell me what you need: property type, location, or budget range."
            ]
            response = random.choice(responses)

    except Exception as e:
        logger.error(f"Chatbot error: {str(e)}")
        response = "😅 I'm having some technical difficulties right now. Please try our 'Browse Houses' page or check back in a few minutes!"
    
    finally:
        # Always close database connections
        try:
            cursor.close()
            conn.close()
        except:
            pass  # Ignore close errors

    logger.info(f"Chatbot response: {response}")
    return jsonify({
        'response': response, 
        'properties': properties[:3]  # Return max 3 properties to frontend
    })

