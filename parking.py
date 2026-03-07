import json
from app import db

class FreeParkingSchedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    day_of_week = db.Column(db.String(20), nullable=False)
    start_time = db.Column(db.String(5), nullable=False)  # Format: HH:MM
    end_time = db.Column(db.String(5), nullable=False)    # Format: HH:MM
    parking_lot_id = db.Column(db.Integer, db.ForeignKey('parking_lot.id'), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "day_of_week": self.day_of_week,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "parking_lot_id": self.parking_lot_id
        }

class SpecialParkingSchedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(10), nullable=False)  # Format: YYYY-MM-DD
    start_time = db.Column(db.String(5), nullable=False)  # Format: HH:MM
    end_time = db.Column(db.String(5), nullable=False)    # Format: HH:MM
    tier = db.Column(db.String(20), nullable=False)  # e.g., "Free", "School", "Meter"
    parking_lot_id = db.Column(db.Integer, db.ForeignKey('parking_lot.id'), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "date": self.date,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "tier": self.tier,
            "parking_lot_id": self.parking_lot_id
        }

class ParkingLot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    spaces = db.Column(db.Integer, nullable=False, default=0)
    # GeoJSON polygon coordinates stored as JSON string
    coordinates = db.Column(db.Text, nullable=False)
    default_tier = db.Column(db.Text, nullable=False)
    owner = db.Column(db.String(100), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "spaces": self.spaces,
            "coordinates": json.loads(self.coordinates),
            "default_tier": self.default_tier,
            "owner": self.owner
        }
