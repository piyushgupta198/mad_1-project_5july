from controllers.database import db
from datetime import datetime

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    address = db.Column(db.String(200), nullable=True)
    pin_code = db.Column(db.String(20), nullable=True)
    full_name = db.Column(db.String(100), nullable=True)
    phone_number = db.Column(db.String(15), nullable=True)

    roles = db.relationship('Role', secondary='user_role')

class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

class UserRole(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), nullable=False)

class ParkingLot(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    location = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    pin_code = db.Column(db.String, nullable=False)
    price = db.Column(db.String, nullable=False)
    max_spots = db.Column(db.Integer, nullable=False)
    spots = db.relationship('ParkingSpot', backref='lot', cascade="all, delete-orphan")

class ParkingSpot(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    lot_id = db.Column(db.Integer, db.ForeignKey('parking_lot.id'), nullable=False)
    status = db.Column(db.String(1), nullable=False, default='A')  
    spot = db.Column(db.String, nullable=False)

class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    spot_id = db.Column(db.Integer, db.ForeignKey('parking_spot.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    parking_timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    leaving_timestamp = db.Column(db.DateTime, nullable=True)
    parking_cost = db.Column(db.Float, nullable=True)
    vehicle_number = db.Column(db.String(20), nullable=False)
    # total_cost = db.Column(db.Float, nullable=True)
    spot = db.relationship('ParkingSpot', backref='reservations')
    user = db.relationship('User', backref='reservations')