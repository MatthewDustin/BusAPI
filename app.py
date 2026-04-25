import os, json, time, logging, shutil
from datetime import datetime
from flask import Flask, render_template, jsonify, request, send_from_directory, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from bus import fetch_data
from sqlalchemy import event

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
app.logger.setLevel(logging.INFO)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///parking.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "your-secret-key-change-this-in-production"
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# Import models after db initialization to avoid circular imports
from parking import ParkingLot, FreeParkingSchedule, SpecialParkingSchedule

# Simple hardcoded user for authentication
class User(UserMixin):
    def __init__(self, username):
        self.id = username
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    if user_id == "admin":
        return User("admin")
    return None

def backup_db(session):
    if os.path.exists('instance/parking.db'):
        shutil.copy('instance/parking.db', 'parking_backup.db')

event.listen(db.session, 'after_commit', backup_db)

with app.app_context():
    if not os.path.exists('instance/parking.db') and os.path.exists('parking_backup.db'):
        shutil.copy('parking_backup.db', 'instance/parking.db')
    db.create_all()

# Delete JSON cache files on app launch to force fresh data fetch from external APIs
files_to_delete = ['announcements.json', 'buses.json', 'routes.json', 'stopETAs.json', 'stops.json', 'vehicles.json']
for file in files_to_delete:
    if os.path.exists(file):
        os.remove(file)

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(app.root_path, 'favicon.ico')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Hardcoded credentials check
        if username == "admin" and password == "parkingyosef3":
            user = User("admin")
            login_user(user)
            return redirect(url_for('lot_manager'))
        else:
            return render_template('login.html', error="Invalid username or password")
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/lotmanager')
@login_required
def lot_manager():
    return render_template('lotManager.html')

@app.route('/parking')
def parking_map():
    return render_template('parking.html')

@app.route("/api/lots", methods=["GET"])
def get_lots():
    lots = ParkingLot.query.all()
    lots_data = [lot.to_dict() for lot in lots]

    answer = jsonify({"time": str(datetime.now().time()), "lots": lots_data})
    return answer

@app.route("/api/lots", methods=["POST"])
def create_lot():
    data = request.get_json()
    if not data or not data.get("name") or not data.get("coordinates"):
        return jsonify({"error": "name and coordinates are required"}), 400

    lot = ParkingLot(
        name=data["name"],
        spaces=int(data.get("spaces", 0)),
        coordinates=json.dumps(data["coordinates"]),
        default_tier=data["default_tier"],
        owner=data.get("owner", None),
        visible=data.get("visible", False)
    )
    db.session.add(lot)
    db.session.commit()
    return jsonify(lot.to_dict()), 201

@app.route("/api/lots/<int:lot_id>", methods=["PUT"])
def update_lot(lot_id):
    lot = ParkingLot.query.get_or_404(lot_id)
    data = request.get_json()

    if "name" in data:
        lot.name = data["name"]
    if "spaces" in data:
        lot.spaces = int(data["spaces"])
    if "coordinates" in data:
        lot.coordinates = json.dumps(data["coordinates"])
    if "default_tier" in data:
        lot.default_tier = data["default_tier"]
    if "owner" in data:
        lot.owner = data["owner"]
    if "visible" in data:
        lot.visible = data["visible"]

    db.session.commit()
    return jsonify(lot.to_dict())

@app.route("/api/lots/<int:lot_id>", methods=["DELETE"])
def delete_lot(lot_id):
    lot = ParkingLot.query.get_or_404(lot_id)
    db.session.delete(lot)
    db.session.commit()
    return jsonify({"deleted": lot_id})

@app.route('/api/schedules/free', methods=["POST"])
def create_free_schedule():
    data = request.get_json()
    if not data or not data.get("day_of_week") or not data.get("parking_lot_id"):
        return jsonify({"error": "day_of_week and parking_lot_id are required"}), 400

    schedule = FreeParkingSchedule(
        day_of_week=data["day_of_week"],
        start_time=data.get("start_time"),
        end_time=data.get("end_time"),
        parking_lot_id=int(data["parking_lot_id"]),
    )
    db.session.add(schedule)
    db.session.commit()
    return jsonify(schedule.to_dict()), 201

@app.route('/api/schedules/special', methods=["POST"])
def create_special_schedule():
    data = request.get_json()
    if not data or not data.get("date") or not data.get("tier") or not data.get("parking_lot_id") or not data.get("repeats"):
        return jsonify({"error": "date, tier, repeats, and parking_lot_id are required"}), 400

    schedule = SpecialParkingSchedule(
        date=data["date"],
        end_date=data.get("end_date"),
        start_time=data.get("start_time"),
        end_time=data.get("end_time"),
        tier=data["tier"],
        repeats=data["repeats"],
        parking_lot_id=int(data["parking_lot_id"]),
    )

    db.session.add(schedule)
    db.session.commit()
    return jsonify(schedule.to_dict()), 201

@app.route('/api/schedules/<int:schedule_id>', methods=["PUT"])
def update_schedule(schedule_id):
    schedule = FreeParkingSchedule.query.get(schedule_id) or SpecialParkingSchedule.query.get(schedule_id)
    if not schedule:
        return jsonify({"error": "Schedule not found"}), 404

    data = request.get_json()
    if isinstance(schedule, FreeParkingSchedule):
        if "day_of_week" in data:
            schedule.day_of_week = data["day_of_week"]
    else:
        if "date" in data:
            schedule.date = data["date"]
        if "end_date" in data:
            schedule.end_date = data["end_date"]
        if "tier" in data:
            schedule.tier = data["tier"]
        if "repeats" in data:
            schedule.repeats = data["repeats"]

    if "start_time" in data:
        schedule.start_time = data["start_time"]
    if "end_time" in data:
        schedule.end_time = data["end_time"]

    db.session.commit()
    return jsonify(schedule.to_dict())

@app.route('/api/schedules/<int:schedule_id>', methods=["DELETE"])
def delete_schedule(schedule_id):
    schedule = FreeParkingSchedule.query.get(schedule_id) or SpecialParkingSchedule.query.get(schedule_id)
    if not schedule:
        return jsonify({"error": "Schedule not found"}), 404

    db.session.delete(schedule)
    db.session.commit()
    return jsonify({"deleted": schedule_id})

@app.route('/announcements')
def get_announcements():
    fetch_data()
    with open('announcements.json', 'r') as file:
        announcements = json.load(file)
        announcements['file_age'] = time.time() - os.path.getmtime('announcements.json')
        return jsonify(announcements)

@app.route('/routes')
def get_routes():
    from bus import routes
    fetch_data()
    with open('routes.json', 'r') as file:
        routes = json.load(file)
        return jsonify(list(routes.values()))

@app.route('/stops')
def get_stops():
    from bus import stops
    fetch_data()
    return jsonify(list(stops.values()))

@app.route('/buses')
def get_buses():
    fetch_data()
    with open('buses.json', 'r') as file:
        buses = json.load(file)
        return jsonify(buses)


if __name__ == "__main__":
     # Railway provides a PORT environment variable automatically
     port = int(os.environ.get('PORT', 8080))
     app.run(host='0.0.0.0', port=port)
