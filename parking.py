from datetime import datetime
import json
from app import db

class FreeParkingSchedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    day_of_week = db.Column(db.String(20), nullable=False)
    start_time = db.Column(db.String(5), nullable=True)  # Format: HH:MM
    end_time = db.Column(db.String(5), nullable=True)    # Format: HH:MM
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
    end_date = db.Column(db.String(10), nullable=True)  # Format: YYYY-MM-DD
    repeats = db.Column(db.String(10), nullable=False)  # Format: "None", "Daily", "Weekly", etc
    start_time = db.Column(db.String(5), nullable=True)  # Format: HH:MM
    end_time = db.Column(db.String(5), nullable=True)    # Format: HH:MM
    tier = db.Column(db.String(64), nullable=False)  # e.g., "Free", "School", "Meter"
    parking_lot_id = db.Column(db.Integer, db.ForeignKey('parking_lot.id'), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "date": self.date,
            "end_date": self.end_date,
            "repeats": self.repeats,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "tier": self.tier,
            "parking_lot_id": self.parking_lot_id
        }

def check_schedules(free, special, default_tier):
    now = datetime.now()
    current_day = now.strftime("%A")
    current_time = now.strftime("%H:%M")
    current_date = now.strftime("%Y-%m-%d")
    tier = default_tier
    #check free schedules first
    for schedule in free:
        if schedule["day_of_week"] == current_day:
            if schedule["start_time"]:
                #format times for comparison
                start_time = datetime.strptime(schedule["start_time"], "%H:%M").time()
                if start_time <= now.time():
                    if schedule["end_time"]:
                        end_time = datetime.strptime(schedule["end_time"], "%H:%M").time()
                        if now.time() <= end_time:
                            tier = "Free"
                    else:
                        tier = "Free"
            else:
                tier = "Free"

    #check special schedules next, which override free schedules
    for schedule in special:
        if schedule["end_date"]:
            end_date = datetime.strptime(schedule["end_date"], "%Y-%m-%d").date()
            if now.date() > end_date:
                continue
        start_date = datetime.strptime(schedule["date"], "%Y-%m-%d").date()
        if now.date() < start_date:
            continue
        if schedule["date"] == current_date:
            if schedule["start_time"] and schedule["start_time"].strip():
                start_time = datetime.strptime(schedule["start_time"], "%H:%M").time()
                if start_time <= now.time():
                    if schedule["end_time"] and schedule["end_time"].strip():
                        end_time = datetime.strptime(schedule["end_time"], "%H:%M").time()
                        if now.time() <= end_time:
                            tier = schedule["tier"]
                    else:
                        tier = schedule["tier"]
            else:
                tier = schedule["tier"]
        elif schedule["repeats"] == "Daily":
            if schedule["start_time"] and schedule["start_time"].strip():
                start_time = datetime.strptime(schedule["start_time"], "%H:%M").time()
                if start_time <= now.time():
                    if schedule["end_time"] and schedule["end_time"].strip():
                        end_time = datetime.strptime(schedule["end_time"], "%H:%M").time()
                        if now.time() <= end_time:
                            tier = schedule["tier"]
                    else:
                        tier = schedule["tier"]
            else:
                tier = schedule["tier"]
        elif schedule["repeats"] == "Weekly":
            #check if today is the same day of week as the original date
            if start_date.strftime("%A") == current_day:
                if schedule["start_time"] and schedule["start_time"].strip():
                    start_time = datetime.strptime(schedule["start_time"], "%H:%M").time()
                    if start_time <= now.time():
                        if schedule["end_time"] and schedule["end_time"].strip():
                            end_time = datetime.strptime(schedule["end_time"], "%H:%M").time()
                            if now.time() <= end_time:
                                tier = schedule["tier"]
                        else:
                            tier = schedule["tier"]
                else:
                    tier = schedule["tier"]
        elif schedule["repeats"] == "Monthly":
            #check if today is the same day of month as the original date
            if start_date.day == now.day:
                if schedule["start_time"] and schedule["start_time"].strip():
                    start_time = datetime.strptime(schedule["start_time"], "%H:%M").time()
                    if start_time <= now.time():
                        if schedule["end_time"] and schedule["end_time"].strip():
                            end_time = datetime.strptime(schedule["end_time"], "%H:%M").time()
                            if now.time() <= end_time:
                                tier = schedule["tier"]
                        else:
                            tier = schedule["tier"]
                else:
                    tier = schedule["tier"]
        elif schedule["repeats"] == "Annually":
            #check if today is the same month and day as the original date
            if start_date.month == now.month and start_date.day == now.day:
                if schedule["start_time"] and schedule["start_time"].strip():
                    start_time = datetime.strptime(schedule["start_time"], "%H:%M").time()
                    if start_time <= now.time():
                        if schedule["end_time"] and schedule["end_time"].strip():
                            end_time = datetime.strptime(schedule["end_time"], "%H:%M").time()
                            if now.time() <= end_time:
                                tier = schedule["tier"]
                        else:
                            tier = schedule["tier"]
                else:
                    tier = schedule["tier"]
    return tier


class ParkingLot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    spaces = db.Column(db.Integer, nullable=False, default=0)
    # GeoJSON polygon coordinates stored as JSON string
    coordinates = db.Column(db.Text, nullable=False)
    default_tier = db.Column(db.String(20), nullable=False)
    owner = db.Column(db.String(100), nullable=True)
    visible = db.Column(db.Boolean, default=True, nullable=False)
    # Relationships
    free_schedules = db.relationship('FreeParkingSchedule', backref='lot', lazy=True, cascade='all, delete-orphan')
    special_schedules = db.relationship('SpecialParkingSchedule', backref='lot', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        free = [s.to_dict() for s in self.free_schedules]
        special = [s.to_dict() for s in self.special_schedules]
        tier = check_schedules(free, special, self.default_tier)
        if "," in tier:
            tier = tier.split(",")
        if "," in self.default_tier:
            default_tier = self.default_tier.split(",")
        else:
            default_tier = self.default_tier

        return {
            "id": self.id,
            "name": self.name,
            "spaces": self.spaces,
            "coordinates": json.loads(self.coordinates),
            "default_tier": default_tier,
            "owner": self.owner,
            "free_schedules": free,
            "special_schedules": special,
            "tier": tier,
            "visible": self.visible
        }
