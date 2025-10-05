# Ghana-Home-Rental
# GhanaRentals - Property Rental Platform

A modern, feature-rich property rental platform built with Flask that connects landlords with tenants in Ghana.

## 🌟 Features

### 👨‍💼 For Landlords
- **Dashboard**: Manage all your properties in one place
- **Add Properties**: Beautiful form with image upload and drag & drop
- **Edit Properties**: Update property details and images
- **Delete Properties**: Remove properties with confirmation
- **Property Management**: View all your listings with status indicators

### 🏠 For Tenants  
- **Browse Properties**: View available rental properties
- **Advanced Filtering**: Filter by region, price range, and property type
- **Property Details**: Detailed view with contact information
- **Responsive Design**: Works perfectly on all devices

### 🔧 For Admins
- **Full System Control**: Manage all properties and users
- **User Management**: Add, edit, and manage user accounts
- **Property Moderation**: Feature properties and manage listings
- **Analytics**: Overview of platform statistics

## 🚀 Tech Stack

- **Backend**: Python, Flask, MySQL
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **Styling**: Custom CSS with modern gradients and animations
- **Database**: MySQL with proper relationships
- **File Upload**: Secure image handling with validation

## 📁 Project Structure

```
ghana-rentals/
├── app.py                 # Main Flask application
├── modules/               # Application modules
│   ├── admin_routes.py    # Admin & landlord routes
│   ├── auth.py           # Authentication system
│   ├── user_routes.py    # Public user routes
│   └── database.py       # Database connection handler
├── templates/            # HTML templates
│   ├── admin/            # Admin interface
│   ├── landlord/         # Landlord dashboard
│   ├── auth/             # Login & registration
│   └── user/             # Public pages
├── static/               # Static assets
│   ├── css/              # Custom stylesheets
│   ├── js/               # JavaScript files
│   └── uploads/          # Property images
└── requirements.txt      # Python dependencies
```

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.8+
- MySQL Server
- pip (Python package manager)

### Step-by-Step Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/ghana-rentals.git
   cd ghana-rentals
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up MySQL database**
   ```sql
   CREATE DATABASE rental_service;
   -- Import the provided SQL schema file
   ```

5. **Configure environment variables**
   Create a `.env` file:
   ```env
   SECRET_KEY=your-secret-key-here
   MYSQL_HOST=localhost
   MYSQL_USER=root
   MYSQL_PASSWORD=your-password
   MYSQL_DB=rental_service
   ```

6. **Run the application**
   ```bash
   python app.py
   ```

7. **Access the application**
   Open your browser and go to: `http://localhost:5000`

## 👥 User Roles & Access

### Tenant
- **Register/Login**: Create account or sign in
- **Browse Properties**: View all available listings
- **Search & Filter**: Find properties by location and price
- **Contact Landlords**: Get contact information for properties

### Landlord
- **Dashboard**: Manage property portfolio
- **Add Properties**: Create new listings with images
- **Edit Listings**: Update property information
- **Track Performance**: View property status

### Admin
- **Full Access**: Manage all system aspects
- **User Management**: Control user accounts and roles
- **Content Moderation**: Feature properties and moderate content
- **System Analytics**: Platform overview and statistics

## 🎨 Features Highlights

### Modern UI/UX
- **Gradient Backgrounds**: Beautiful visual design
- **Glass Morphism**: Modern glass-like effects
- **Responsive Design**: Works on all screen sizes
- **Smooth Animations**: Enhanced user experience

### Advanced Functionality
- **Image Upload**: Drag & drop with preview
- **Form Validation**: Client and server-side validation
- **Session Management**: Secure user sessions
- **Role-Based Access**: Different interfaces per user type

### Security Features
- **Password Hashing**: Secure password storage
- **SQL Injection Protection**: Parameterized queries
- **File Upload Security**: Validated image uploads
- **Session Protection**: Secure authentication system

## 📞 Contact & Support

- **Developer**: Hamdan Salifu Polibu
- **Email**: [hamdansalifupolibu@gmail.com](mailto:hamdansalifupolibu@gmail.com)


## 🤝 Contributing

We welcome contributions! Please feel free to submit pull requests, report bugs, or suggest new features.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.

## 🚀 Deployment

### For Production Deployment

1. **Set up production server** (Ubuntu example):
   ```bash
   sudo apt update
   sudo apt install python3-pip python3-venv nginx mysql-server
   ```

2. **Configure production environment**:
   ```bash
   export FLASK_ENV=production
   export SECRET_KEY=your-production-secret-key
   ```

3. **Use production WSGI server**:
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```

---

**Built with ❤️ for the Ghana rental market**

*Making property rental simple, secure, and efficient*
