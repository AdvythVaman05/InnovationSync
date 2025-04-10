from flask import Flask, request, render_template, redirect, url_for, flash, session, jsonify
from flask_pymongo import PyMongo
from bson import ObjectId
import os

# Flask app setup
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'supersecretkey')
app.config['MONGO_URI'] = os.getenv('MONGO_URI', 'mongodb://localhost:27017/synthetic_ehr')

# Initialize PyMongo
mongo = PyMongo(app)
db = mongo.cx.get_database('synthetic_ehr')

# Confirm DB connection
try:
    print("✅ Connected to MongoDB:", db.name)
except Exception as e:
    print("❌ MongoDB connection failed:", str(e))
    raise

# Serve HTML frontend
@app.route('/', methods=['GET'])
def index():
    return render_template("index.html")

# Handle login request via JS fetch
@app.route('/login', methods=['POST'])
def login():
    role = request.form.get("role")
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()
    
    if not role or not username or not password:
        return jsonify({"success": False, "message": "All fields are required."}), 400
    
    # Use 'username' field instead of 'email'
    if role == 'admin':
        user = db.admin_login.find_one({"username": username, "password": password})
    elif role == 'doctor':
        user = db.doctor_login.find_one({"username": username, "password": password})
    else:
        return jsonify({"success": False, "message": "Invalid role."}), 400
    
    if user:
        session['user_id'] = str(user['_id'])
        session['user_role'] = role
        session['username'] = username
        
        return jsonify({
            "success": True,
            "message": f"{role.capitalize()} login successful.",
            "role": role,
            "username": username
        })
    else:
        return jsonify({"success": False, "message": "Invalid username or password."}), 401

# Logout endpoint
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# Health check
@app.route('/health')
def health_check():
    try:
        mongo.db.command('ping')
        return "Database connection working!", 200
    except Exception as e:
        return f"Database connection failed: {str(e)}", 500

# Make sure template directory exists
os.makedirs('templates', exist_ok=True)

# Run app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)