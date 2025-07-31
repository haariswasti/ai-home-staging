#!/usr/bin/env python3
"""
AI Home Staging Web Application
Flask-based web app for AI-powered bedroom staging recommendations
"""

import os
import sys
import secrets
from datetime import datetime
from pathlib import Path

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import numpy as np
import torch
import json
from bs4 import BeautifulSoup
import requests
import tempfile
from werkzeug.middleware.proxy_fix import ProxyFix

from src.data_loader import load_image
from src.feature_extractor import FeatureExtractor
from src.retrieval import retrieve

# Initialize Flask app
app = Flask(__name__)

# Production configuration
if os.environ.get('RENDER'):
    # Production settings for Render
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-this')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///home_staging.db')
    app.config['UPLOAD_FOLDER'] = '/opt/render/project/src/uploads'
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
else:
    # Development settings
    app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///home_staging.db'
    app.config['UPLOAD_FOLDER'] = 'uploads'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize database
db = SQLAlchemy(app)

# Global variables for AI model and embeddings
model = None
staged_embeddings = None
staged_names = None

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    uploads = db.relationship('Upload', backref='user', lazy=True)

class Upload(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    similarity_scores = db.Column(db.Text)  # JSON string of results

class Inventory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_type = db.Column(db.String(50), nullable=False)  # chairs, beds, bedframe, etc.
    quantity = db.Column(db.Integer, default=0)
    description = db.Column(db.String(200))
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class House(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(50), default='upcoming')  # upcoming, staged, completed
    scheduled_date = db.Column(db.DateTime, nullable=True)
    staged_date = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    num_bedrooms = db.Column(db.Integer, default=0)
    num_living_rooms = db.Column(db.Integer, default=0)
    num_dining_rooms = db.Column(db.Integer, default=0)
    house_inventory = db.relationship('HouseInventory', back_populates='house', cascade='all, delete-orphan')

class HouseInventory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    house_id = db.Column(db.Integer, db.ForeignKey('house.id'), nullable=False)
    inventory_id = db.Column(db.Integer, db.ForeignKey('inventory.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    house = db.relationship('House', back_populates='house_inventory')
    inventory = db.relationship('Inventory')

# Initialize AI model
print("🤖 Loading AI model...")
model = FeatureExtractor()
model.eval()

# Load staged bedroom embeddings
print("📊 Loading staged bedroom embeddings...")
staged_embs = np.load('models/staged_embs.npy')
staged_names = np.load('models/staged_names.npy')
print(f"✅ Loaded {len(staged_embs)} staged bedroom embeddings")

ROOM_TYPES = ['bedroom', 'living_room', 'dining_room', 'office', 'outdoor']

def allowed_file(filename):
    """Check if file extension is allowed"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_image(image_path, room_type='bedroom'):
    """Process uploaded image and find similar staged rooms of the selected type"""
    global model
    try:
        # Load model on first use to save memory
        if model is None:
            print("🤖 Loading AI model...")
            model = FeatureExtractor()
            model.eval()
            print("✅ AI model loaded successfully")
        
        # Load and process image
        img = load_image(image_path).unsqueeze(0)
        # Extract features
        with torch.no_grad():
            query_emb = model(img).cpu().numpy()
        # Load correct staged embeddings for the room type
        emb_path = f'models/staged_{room_type}_embs.npy'
        names_path = f'models/staged_{room_type}_names.npy'
        if not os.path.exists(emb_path) or not os.path.exists(names_path):
            return f"No staged reference images found for room type '{room_type}'. Please add staged images and generate embeddings."
        staged_embs = np.load(emb_path)
        staged_names = np.load(names_path)
        # Find similar staged rooms
        idxs, sims = retrieve(query_emb, staged_embs, top_k=3)
        results = []
        for i, (idx, sim) in enumerate(zip(idxs, sims)):
            results.append({
                'rank': i + 1,
                'image_name': staged_names[idx],
                'similarity': float(sim),
                'image_path': f'staged/{room_type}/{staged_names[idx]}'
            })
        return results
    except Exception as e:
        print(f"Error processing image: {e}")
        return None

def guess_room_type(filename_or_url):
    name = filename_or_url.lower()
    
    # Outdoor/Exterior indicators
    outdoor_keywords = ['outdoor', 'patio', 'balcony', 'deck', 'terrace', 'garden', 'yard', 'backyard', 
                       'frontyard', 'exterior', 'outside', 'outdoor', 'pool', 'spa', 'bbq', 'grill']
    for keyword in outdoor_keywords:
        if keyword in name:
            return 'outdoor'
    
    # Living room indicators
    living_keywords = ['living', 'family', 'great', 'main', 'sitting', 'lounge', 'tv', 'entertainment']
    for keyword in living_keywords:
        if keyword in name:
            return 'living_room'
    
    # Dining room indicators
    dining_keywords = ['dining', 'eat', 'kitchen', 'breakfast', 'nook', 'table']
    for keyword in dining_keywords:
        if keyword in name:
            return 'dining_room'
    
    # Office indicators
    office_keywords = ['office', 'study', 'work', 'desk', 'computer', 'home office']
    for keyword in office_keywords:
        if keyword in name:
            return 'office'
    
    # Bathroom indicators
    bathroom_keywords = ['bath', 'bathroom', 'toilet', 'shower', 'powder']
    for keyword in bathroom_keywords:
        if keyword in name:
            return 'bathroom'
    
    # Bedroom indicators (more specific)
    bedroom_keywords = ['bed', 'sleep', 'master', 'guest', 'kids', 'nursery', 'bedroom']
    for keyword in bedroom_keywords:
        if keyword in name:
            return 'bedroom'
    
    # If no clear indicators, try to make a more educated guess
    # Check if it's likely outdoor based on common outdoor image patterns
    if any(word in name for word in ['zillow', 'redfin', 'listing', 'property', 'house', 'home']):
        # For real estate listings, check if it might be exterior
        if any(word in name for word in ['front', 'back', 'side', 'exterior', 'outside']):
            return 'outdoor'
    
    # Default to bedroom as fallback
    return 'bedroom'

# Helper function to calculate inventory requirements
def calculate_inventory_requirements(king_bedrooms=0, queen_bedrooms=0, full_bedrooms=0, twin_bedrooms=0,
                                   living_rooms=0, dining_rooms=0, offices=0, outdoor_rooms=0,
                                   bench_or_chairs_king=False, bench_or_chairs_queen=False,
                                   outdoor_bench=False, extra_nightstand_twin=False,
                                   twin_desk_chair=False, twin_teepee=False, twin_toybasket=False,
                                   loveseat=False, dining_chair_count=4, dining_table_shape='rectangle',
                                   dining_table_type='glass', dining_table_size='60'):
    """Calculate inventory requirements based on room types and options"""
    requirements = {}

    # King Bedrooms
    if king_bedrooms > 0:
        requirements['bed_king'] = king_bedrooms
        requirements['mattress_king'] = king_bedrooms
        requirements['headboard_king'] = king_bedrooms
        requirements['nightstand_king'] = king_bedrooms * 2
        requirements['rug_king'] = king_bedrooms
        requirements['plant_king'] = king_bedrooms
        requirements['wall_art_king'] = king_bedrooms
        requirements['decor_king'] = king_bedrooms
        if bench_or_chairs_king:
            requirements['accent_chair_king'] = king_bedrooms * 2
            requirements['accent_table_king'] = king_bedrooms
        else:
            requirements['bench_king'] = king_bedrooms

    # Queen Bedrooms
    if queen_bedrooms > 0:
        requirements['bed_queen'] = queen_bedrooms
        requirements['mattress_queen'] = queen_bedrooms
        requirements['headboard_queen'] = queen_bedrooms
        requirements['nightstand_queen'] = queen_bedrooms * 2
        requirements['rug_queen'] = queen_bedrooms
        requirements['plant_queen'] = queen_bedrooms
        requirements['wall_art_queen'] = queen_bedrooms
        requirements['decor_queen'] = queen_bedrooms
        if bench_or_chairs_queen:
            requirements['accent_chair_queen'] = queen_bedrooms * 2
            requirements['accent_table_queen'] = queen_bedrooms
        else:
            requirements['bench_queen'] = queen_bedrooms

    # Full Bedrooms
    if full_bedrooms > 0:
        requirements['bed_full'] = full_bedrooms
        requirements['mattress_full'] = full_bedrooms
        requirements['headboard_full'] = full_bedrooms
        requirements['nightstand_full'] = full_bedrooms * 2
        requirements['rug_full'] = full_bedrooms
        requirements['accent_table_full'] = full_bedrooms
        requirements['plant_full'] = full_bedrooms
        requirements['wall_art_full'] = full_bedrooms
        requirements['decor_full'] = full_bedrooms

    # Twin Bedrooms
    if twin_bedrooms > 0:
        requirements['bed_twin'] = twin_bedrooms
        requirements['mattress_twin'] = twin_bedrooms
        requirements['headboard_twin'] = twin_bedrooms
        requirements['nightstand_twin'] = twin_bedrooms * (2 if extra_nightstand_twin else 1)
        requirements['rug_twin'] = twin_bedrooms
        requirements['plant_twin'] = twin_bedrooms
        requirements['wall_art_twin'] = twin_bedrooms
        requirements['decor_twin'] = twin_bedrooms
        if twin_desk_chair:
            requirements['desk_twin'] = twin_bedrooms
            requirements['chair_twin'] = twin_bedrooms
        if twin_teepee:
            requirements['teepee_twin'] = twin_bedrooms
        if twin_toybasket:
            requirements['toybasket_twin'] = twin_bedrooms

    # Living Rooms
    if living_rooms > 0:
        requirements['couch'] = living_rooms
        requirements['side_table'] = living_rooms * 2
        requirements['accent_chair_living'] = living_rooms * 2
        requirements['coffee_table'] = living_rooms
        requirements['wall_art_living'] = living_rooms
        requirements['decor_living'] = living_rooms
        if loveseat:
            requirements['loveseat'] = living_rooms

    # Dining Rooms
    if dining_rooms > 0:
        requirements['dining_table'] = dining_rooms
        requirements['dining_chair'] = dining_rooms * dining_chair_count
        requirements['wall_art_dining'] = dining_rooms
        requirements['decor_dining'] = dining_rooms
        requirements['dining_table_shape'] = f"{dining_table_shape} ({dining_table_type}, {dining_table_size}) x{dining_rooms}"

    # Offices
    if offices > 0:
        requirements['desk'] = offices
        requirements['rug_office'] = offices
        requirements['office_chair'] = offices
        requirements['plant_office'] = offices
        requirements['wall_art_office'] = offices
        requirements['decor_office'] = offices

    # Outdoor Rooms
    if outdoor_rooms > 0:
        requirements['outdoor_rug'] = outdoor_rooms
        requirements['outdoor_table'] = outdoor_rooms
        requirements['outdoor_chair'] = outdoor_rooms * 2
        requirements['wall_art_outdoor'] = outdoor_rooms
        requirements['decor_outdoor'] = outdoor_rooms
        if outdoor_bench:
            requirements['outdoor_bench'] = outdoor_rooms

    return requirements

# Helper function to extract images from a listing URL

def extract_images_from_listing(url, room_type):
    """Download images from a real estate listing page. Returns list of local file paths."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            return [], f"Failed to fetch listing page (status {resp.status_code})"
        soup = BeautifulSoup(resp.text, 'html.parser')
        # Try to find all <img> tags with src containing jpg/jpeg/png
        img_tags = soup.find_all('img')
        img_urls = [img['src'] for img in img_tags if img.get('src') and any(ext in img['src'] for ext in ['.jpg', '.jpeg', '.png'])]
        # Remove duplicates and filter out tiny images
        img_urls = list({u for u in img_urls if not u.startswith('data:') and not u.endswith('.svg')})
        if not img_urls:
            return [], "No images found on the listing page."
        # Download images to temp files
        local_paths = []
        for i, img_url in enumerate(img_urls):
            try:
                img_resp = requests.get(img_url, headers=headers, timeout=10)
                if img_resp.status_code == 200:
                    ext = img_url.split('.')[-1].split('?')[0]
                    with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{ext}') as f:
                        f.write(img_resp.content)
                        local_paths.append(f.name)
            except Exception as e:
                continue
        if not local_paths:
            return [], "Failed to download any images from the listing."
        return local_paths, None
    except Exception as e:
        return [], f"Error extracting images: {e}"

# Routes
@app.route('/')
def index():
    if 'user_id' not in session:
        return render_template('index.html')
    user = User.query.get(session['user_id'])
    uploads = Upload.query.filter_by(user_id=user.id).order_by(Upload.uploaded_at.desc()).limit(10)
    inventory_items = Inventory.query.all()
    # Dashboard stats
    total_houses = House.query.count()
    staged_houses = House.query.filter_by(status='staged').count()
    upcoming_houses = House.query.filter_by(status='upcoming').count()
    completed_houses = House.query.filter_by(status='completed').count()
    inventory_in_use = db.session.query(db.func.sum(HouseInventory.quantity)).join(House).filter(House.status=='staged').scalar() or 0
    return render_template('index.html', user=user, uploads=uploads, inventory_items=inventory_items,
                           total_houses=total_houses, staged_houses=staged_houses, upcoming_houses=upcoming_houses,
                           completed_houses=completed_houses, inventory_in_use=inventory_in_use)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists!', 'error')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered!', 'error')
            return redirect(url_for('register'))
        
        # Create new user
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash('Login successful! Welcome to AI Home Staging!', 'success')
            return redirect(url_for('upload'))
        else:
            flash('Invalid username or password!', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """User logout"""
    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/houses')
def houses():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    houses = House.query.order_by(House.scheduled_date.desc().nullslast(), House.staged_date.desc().nullslast()).all()
    inventory = Inventory.query.all()
    return render_template('houses.html', houses=houses, inventory=inventory)

@app.route('/houses/add', methods=['GET', 'POST'])
def add_house():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    inventory = Inventory.query.all()
    if request.method == 'POST':
        name = request.form['name']
        address = request.form.get('address')
        status = request.form.get('status', 'upcoming')
        scheduled_date = request.form.get('scheduled_date')
        notes = request.form.get('notes')
        num_bedrooms = int(request.form.get('num_bedrooms', 0))
        num_living_rooms = int(request.form.get('num_living_rooms', 0))
        num_dining_rooms = int(request.form.get('num_dining_rooms', 0))
        
        # Get room type breakdown for Pre-Stage Helper logic
        king_bedrooms = int(request.form.get('king_bedrooms', 0))
        queen_bedrooms = int(request.form.get('queen_bedrooms', 0))
        full_bedrooms = int(request.form.get('full_bedrooms', 0))
        twin_bedrooms = int(request.form.get('twin_bedrooms', 0))
        offices = int(request.form.get('offices', 0))
        outdoor_rooms = int(request.form.get('outdoor_rooms', 0))
        
        # Get option toggles
        bench_or_chairs_king = 'bedroom_bench_or_chairs' in request.form and king_bedrooms > 0
        bench_or_chairs_queen = 'bedroom_bench_or_chairs' in request.form and queen_bedrooms > 0
        outdoor_bench = 'outdoor_bench' in request.form
        extra_nightstand_twin = 'extra_nightstand_twin' in request.form
        twin_desk_chair = 'twin_desk_chair' in request.form
        twin_teepee = 'twin_teepee' in request.form
        twin_toybasket = 'twin_toybasket' in request.form
        loveseat = 'loveseat' in request.form
        dining_chair_count = int(request.form.get('dining_chair_count', 4))
        dining_table_shape = request.form.get('dining_table_shape', 'rectangle')
        dining_table_type = request.form.get('dining_table_type', 'glass')
        dining_table_size = request.form.get('dining_table_size', '60')
        
        house = House(name=name, address=address, status=status, notes=notes,
                      num_bedrooms=num_bedrooms, num_living_rooms=num_living_rooms, num_dining_rooms=num_dining_rooms)
        if scheduled_date:
            house.scheduled_date = datetime.strptime(scheduled_date, '%Y-%m-%d')
        db.session.add(house)
        db.session.commit()
        
        # Use Pre-Stage Helper logic to calculate inventory requirements
        requirements = calculate_inventory_requirements(
            king_bedrooms=king_bedrooms,
            queen_bedrooms=queen_bedrooms,
            full_bedrooms=full_bedrooms,
            twin_bedrooms=twin_bedrooms,
            living_rooms=num_living_rooms,
            dining_rooms=num_dining_rooms,
            offices=offices,
            outdoor_rooms=outdoor_rooms,
            bench_or_chairs_king=bench_or_chairs_king,
            bench_or_chairs_queen=bench_or_chairs_queen,
            outdoor_bench=outdoor_bench,
            extra_nightstand_twin=extra_nightstand_twin,
            twin_desk_chair=twin_desk_chair,
            twin_teepee=twin_teepee,
            twin_toybasket=twin_toybasket,
            loveseat=loveseat,
            dining_chair_count=dining_chair_count,
            dining_table_shape=dining_table_shape,
            dining_table_type=dining_table_type,
            dining_table_size=dining_table_size
        )
        
        # Assign inventory based on calculated requirements
        for item_type, quantity in requirements.items():
            if isinstance(quantity, int) and quantity > 0:
                item = Inventory.query.filter_by(item_type=item_type).first()
                if item:
                    hi = HouseInventory(house_id=house.id, inventory_id=item.id, quantity=quantity)
                    db.session.add(hi)
                    # Subtract from warehouse if staged
                    if status == 'staged':
                        item.quantity = max(0, item.quantity - quantity)
        
        # Also handle manual inventory assignments if provided
        for item in inventory:
            qty = int(request.form.get(f'inventory_{item.id}', 0))
            if qty > 0:
                # Check if already assigned by Pre-Stage Helper
                existing = HouseInventory.query.filter_by(house_id=house.id, inventory_id=item.id).first()
                if existing:
                    existing.quantity += qty
                else:
                    hi = HouseInventory(house_id=house.id, inventory_id=item.id, quantity=qty)
                    db.session.add(hi)
                # Subtract from warehouse if staged
                if status == 'staged':
                    item.quantity = max(0, item.quantity - qty)
        
        db.session.commit()
        flash('House added successfully with Pre-Stage Helper inventory calculation!', 'success')
        return redirect(url_for('houses'))
    return render_template('add_house.html', inventory=inventory)

@app.route('/houses/<int:house_id>/stage', methods=['POST'])
def stage_house(house_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    house = House.query.get_or_404(house_id)
    if house.status != 'staged':
        house.status = 'staged'
        house.staged_date = datetime.utcnow()
        # Subtract inventory
        for hi in house.house_inventory:
            item = Inventory.query.get(hi.inventory_id)
            if item:
                item.quantity = max(0, item.quantity - hi.quantity)
        db.session.commit()
        flash('House marked as staged and inventory subtracted.', 'success')
    return redirect(url_for('houses'))

@app.route('/houses/<int:house_id>/complete', methods=['POST'])
def complete_house(house_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    house = House.query.get_or_404(house_id)
    if house.status != 'completed':
        house.status = 'completed'
        # Return inventory
        for hi in house.house_inventory:
            item = Inventory.query.get(hi.inventory_id)
            if item:
                item.quantity += hi.quantity
        db.session.commit()
        flash('House marked as completed and inventory returned.', 'success')
    return redirect(url_for('houses'))

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        file = request.files.get('file')
        room_type = request.form.get('room_type', 'auto')
        if room_type != 'auto' and room_type not in ROOM_TYPES:
            flash('Invalid room type selected!', 'error')
            return redirect(request.url)
        if not file or file.filename == '':
            flash('No file selected!', 'error')
            return redirect(request.url)
        rt = room_type
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            unique_filename = f"{timestamp}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(filepath)
            results = process_image(filepath, room_type=rt)
            if isinstance(results, str):
                flash(results, 'error')
                return redirect(request.url)
            if results:
                upload_record = Upload(
                    user_id=session['user_id'],
                    filename=unique_filename,
                    original_filename=filename,
                    similarity_scores=json.dumps(results)
                )
                db.session.add(upload_record)
                db.session.commit()
                flash('Image uploaded and processed successfully!', 'success')
                user = User.query.get(session['user_id'])
                inventory_items = Inventory.query.all()
                return render_template('dashboard.html', results=results, user=user, uploaded_filename=unique_filename, inventory_items=inventory_items)
            else:
                flash('Error processing image!', 'error')
                return redirect(request.url)
    return render_template('upload.html', room_types=ROOM_TYPES)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Serve uploaded files"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/data/<path:filename>')
def data_file(filename):
    """Serve data files (staged bedroom images)"""
    return send_from_directory('data', filename)

@app.route('/inventory')
def inventory():
    """Inventory management page"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Get all inventory items
    items = Inventory.query.all()
    
    # If no items exist, create default inventory
    if not items:
        default_items = [
            # Beds and frames
            'king bed', 'queen bed', 'full bed', 'twin bed',
            'king mattress', 'queen mattress', 'full mattress', 'twin mattress',
            'king headboard', 'queen headboard', 'full headboard', 'twin headboard',
            'metal frame',
            # Nightstands and tables
            'night stand', 'nightstand_king', 'nightstand_queen', 'nightstand_full', 'nightstand_twin',
            'end table', 'accent table_king', 'accent table_queen', 'accent table_full', 'side table',
            'coffee table',
            # Couches and seating
            'big couch', 'midsize couch', 'loveseat', 'couch', 'accent chair_king', 'accent chair_queen', 'accent chair_living',
            'bench_king', 'bench_queen', 'bench', 'outdoor bench',
            # Dining
            'dining table', 'dining chair',
            # Office and storage
            'desk', 'desk_twin', 'office chair', 'chair_twin', 'console', 'credenza', 'media console',
            # Kids
            'kiddie stool', 'kiddie shelving unit', 'teepee_twin', 'toybasket_twin', 'toys',
            # Rugs
            'indoor rug 5x7', 'indoor rug 6x9', 'indoor rug 8x10',
            'outdoor rug 5x7', 'outdoor rug 6x9', 'outdoor rug 8x10', 'rug_king', 'rug_queen', 'rug_full', 'rug_twin', 'rug_office', 'outdoor_rug',
            # Outdoor
            'outdoor furniture', 'outdoor table', 'outdoor chair',
            # Decor and art
            'plant_king', 'plant_queen', 'plant_full', 'plant_twin', 'plant_office',
            'wall art_king', 'wall art_queen', 'wall art_full', 'wall art_twin', 'wall art_living', 'wall art_dining', 'wall art_office', 'wall art_outdoor',
            'decor_king', 'decor_queen', 'decor_full', 'decor_twin', 'decor_living', 'decor_dining', 'decor_office', 'decor_outdoor'
        ]
        for item_type in default_items:
            item = Inventory(item_type=item_type, quantity=0, description=f'Available {item_type.replace("_", " ")} for staging')
            db.session.add(item)
        db.session.commit()
        items = Inventory.query.all()
    
    return render_template('inventory.html', items=items)

@app.route('/inventory/update', methods=['POST'])
def update_inventory():
    """Update inventory quantities"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    item_id = request.form.get('item_id')
    quantity = request.form.get('quantity')
    description = request.form.get('description')
    
    if item_id and quantity is not None:
        item = Inventory.query.get(item_id)
        if item:
            item.quantity = int(quantity)
            if description:
                item.description = description
            db.session.commit()
            flash('Inventory updated successfully!', 'success')
        else:
            flash('Item not found!', 'error')
    else:
        flash('Invalid data provided!', 'error')
    
    return redirect(url_for('inventory'))

@app.route('/inventory/add', methods=['POST'])
def add_inventory_item():
    """Add new inventory item"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    item_type = request.form.get('item_type')
    quantity = request.form.get('quantity', 0)
    description = request.form.get('description', '')
    
    if item_type:
        # Check if item already exists
        existing = Inventory.query.filter_by(item_type=item_type).first()
        if existing:
            flash('Item type already exists!', 'error')
        else:
            item = Inventory(
                item_type=item_type,
                quantity=int(quantity),
                description=description
            )
            db.session.add(item)
            db.session.commit()
            flash('New item added to inventory!', 'success')
    else:
        flash('Item type is required!', 'error')
    
    return redirect(url_for('inventory'))

@app.route('/inventory/delete/<int:item_id>')
def delete_inventory_item(item_id):
    """Delete inventory item"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    item = Inventory.query.get(item_id)
    if item:
        db.session.delete(item)
        db.session.commit()
        flash('Item deleted from inventory!', 'success')
    else:
        flash('Item not found!', 'error')
    
    return redirect(url_for('inventory'))

@app.route('/prestage')
def prestage():
    """Pre-staging helper page"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Get current inventory for comparison
    inventory_items = Inventory.query.all()
    inventory_dict = {item.item_type: item.quantity for item in inventory_items}
    
    return render_template('prestage.html', inventory=inventory_dict)

@app.route('/prestage/calculate', methods=['POST'])
def calculate_prestage():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    king_bedrooms = int(request.form.get('king_bedrooms', 0))
    queen_bedrooms = int(request.form.get('queen_bedrooms', 0))
    full_bedrooms = int(request.form.get('full_bedrooms', 0))
    twin_bedrooms = int(request.form.get('twin_bedrooms', 0))
    living_rooms = int(request.form.get('living_rooms', 0))
    dining_rooms = int(request.form.get('dining_rooms', 0))
    offices = int(request.form.get('offices', 0))
    outdoor_rooms = int(request.form.get('outdoor_rooms', 0))

    # Option toggles
    bench_or_chairs_king = 'bedroom_bench_or_chairs' in request.form and king_bedrooms > 0
    bench_or_chairs_queen = 'bedroom_bench_or_chairs' in request.form and queen_bedrooms > 0
    outdoor_bench = 'outdoor_bench' in request.form
    extra_nightstand_twin = 'extra_nightstand_twin' in request.form
    twin_desk_chair = 'twin_desk_chair' in request.form
    twin_teepee = 'twin_teepee' in request.form
    twin_toybasket = 'twin_toybasket' in request.form
    loveseat = 'loveseat' in request.form
    # Dining room options
    dining_chair_count = int(request.form.get('dining_chair_count', 4))
    dining_table_shape = request.form.get('dining_table_shape', 'rectangle')
    dining_table_type = request.form.get('dining_table_type', 'glass')
    dining_table_size = request.form.get('dining_table_size', '60')

    requirements = calculate_inventory_requirements(
        king_bedrooms=king_bedrooms,
        queen_bedrooms=queen_bedrooms,
        full_bedrooms=full_bedrooms,
        twin_bedrooms=twin_bedrooms,
        living_rooms=living_rooms,
        dining_rooms=dining_rooms,
        offices=offices,
        outdoor_rooms=outdoor_rooms,
        bench_or_chairs_king=bench_or_chairs_king,
        bench_or_chairs_queen=bench_or_chairs_queen,
        outdoor_bench=outdoor_bench,
        extra_nightstand_twin=extra_nightstand_twin,
        twin_desk_chair=twin_desk_chair,
        twin_teepee=twin_teepee,
        twin_toybasket=twin_toybasket,
        loveseat=loveseat,
        dining_chair_count=dining_chair_count,
        dining_table_shape=dining_table_shape,
        dining_table_type=dining_table_type,
        dining_table_size=dining_table_size
    )

    # Get current inventory for comparison
    inventory_items = Inventory.query.all()
    inventory_dict = {item.item_type: item.quantity for item in inventory_items}

    # Calculate shortages
    shortages = {}
    for item, needed in requirements.items():
        if isinstance(needed, int):
            current = inventory_dict.get(item, 0)
            if needed > current:
                shortages[item] = needed - current

    return render_template('prestage_results.html', 
                         requirements=requirements,
                         inventory=inventory_dict,
                         shortages=shortages,
                         room_counts={
                             'king_bedrooms': king_bedrooms,
                             'queen_bedrooms': queen_bedrooms,
                             'full_bedrooms': full_bedrooms,
                             'twin_bedrooms': twin_bedrooms,
                             'living_rooms': living_rooms,
                             'dining_rooms': dining_rooms,
                             'offices': offices,
                             'outdoor_rooms': outdoor_rooms,
                             'dining_chair_count': dining_chair_count,
                             'dining_table_shape': dining_table_shape,
                             'dining_table_type': dining_table_type,
                             'dining_table_size': dining_table_size
                         })

@app.route('/prestage/create_houses', methods=['POST'])
def create_houses_from_prestage():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    king_bedrooms = int(request.form.get('king_bedrooms', 0))
    queen_bedrooms = int(request.form.get('queen_bedrooms', 0))
    full_bedrooms = int(request.form.get('full_bedrooms', 0))
    twin_bedrooms = int(request.form.get('twin_bedrooms', 0))
    living_rooms = int(request.form.get('living_rooms', 0))
    dining_rooms = int(request.form.get('dining_rooms', 0))
    offices = int(request.form.get('offices', 0))
    outdoor_rooms = int(request.form.get('outdoor_rooms', 0))

    # Option toggles
    bench_or_chairs_king = 'bedroom_bench_or_chairs' in request.form and king_bedrooms > 0
    bench_or_chairs_queen = 'bedroom_bench_or_chairs' in request.form and queen_bedrooms > 0
    outdoor_bench = 'outdoor_bench' in request.form
    extra_nightstand_twin = 'extra_nightstand_twin' in request.form
    twin_desk_chair = 'twin_desk_chair' in request.form
    twin_teepee = 'twin_teepee' in request.form
    twin_toybasket = 'twin_toybasket' in request.form
    loveseat = 'loveseat' in request.form
    # Dining room options
    dining_chair_count = int(request.form.get('dining_chair_count', 4))
    dining_table_shape = request.form.get('dining_table_shape', 'rectangle')
    dining_table_type = request.form.get('dining_table_type', 'glass')
    dining_table_size = request.form.get('dining_table_size', '60')

    requirements = calculate_inventory_requirements(
        king_bedrooms=king_bedrooms,
        queen_bedrooms=queen_bedrooms,
        full_bedrooms=full_bedrooms,
        twin_bedrooms=twin_bedrooms,
        living_rooms=living_rooms,
        dining_rooms=dining_rooms,
        offices=offices,
        outdoor_rooms=outdoor_rooms,
        bench_or_chairs_king=bench_or_chairs_king,
        bench_or_chairs_queen=bench_or_chairs_queen,
        outdoor_bench=outdoor_bench,
        extra_nightstand_twin=extra_nightstand_twin,
        twin_desk_chair=twin_desk_chair,
        twin_teepee=twin_teepee,
        twin_toybasket=twin_toybasket,
        loveseat=loveseat,
        dining_chair_count=dining_chair_count,
        dining_table_shape=dining_table_shape,
        dining_table_type=dining_table_type,
        dining_table_size=dining_table_size
    )

    # Get current inventory for comparison
    inventory_items = Inventory.query.all()
    inventory_dict = {item.item_type: item.quantity for item in inventory_items}

    # Calculate shortages
    shortages = {}
    for item, needed in requirements.items():
        if isinstance(needed, int):
            current = inventory_dict.get(item, 0)
            if needed > current:
                shortages[item] = needed - current

    # Create houses based on requirements
    for i in range(1, 5): # Create up to 4 houses
        house_name = f"House {i}"
        house_address = f"Address {i}"
        house_status = "upcoming"
        house_notes = f"Notes for House {i}"
        house_num_bedrooms = 0
        house_num_living_rooms = 0
        house_num_dining_rooms = 0

        if i == 1:
            house_num_bedrooms = king_bedrooms
            house_num_living_rooms = living_rooms
            house_num_dining_rooms = dining_rooms
        elif i == 2:
            house_num_bedrooms = queen_bedrooms
            house_num_living_rooms = living_rooms
            house_num_dining_rooms = dining_rooms
        elif i == 3:
            house_num_bedrooms = full_bedrooms
            house_num_living_rooms = living_rooms
            house_num_dining_rooms = dining_rooms
        elif i == 4:
            house_num_bedrooms = twin_bedrooms
            house_num_living_rooms = living_rooms
            house_num_dining_rooms = dining_rooms

        house = House(
            name=house_name,
            address=house_address,
            status=house_status,
            notes=house_notes,
            num_bedrooms=house_num_bedrooms,
            num_living_rooms=house_num_living_rooms,
            num_dining_rooms=house_num_dining_rooms
        )
        db.session.add(house)
        db.session.commit()

        # Assign inventory to the newly created house
        for item_type, quantity in requirements.items():
            if isinstance(quantity, int) and quantity > 0:
                item = Inventory.query.filter_by(item_type=item_type).first()
                if item:
                    hi = HouseInventory(house_id=house.id, inventory_id=item.id, quantity=quantity)
                    db.session.add(hi)
                    # Subtract from warehouse if staged
                    if house_status == 'staged':
                        item.quantity = max(0, item.quantity - quantity)
        db.session.commit()

    flash(f'{len(requirements)} houses created based on pre-staging requirements!', 'success')
    return redirect(url_for('houses'))

if __name__ == '__main__':
    # Get port from environment variable (for Render) or default to 5000
    port = int(os.environ.get('PORT', 5000))
    
    # Create uploads directory if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    print("🚀 Starting AI Home Staging Web Application...")
    print(f"📱 Open your browser to: http://localhost:{port}")
    print("🤖 AI model will be loaded on first use to save memory...")
    
    # Run the app
    app.run(host='0.0.0.0', port=port, debug=False) 