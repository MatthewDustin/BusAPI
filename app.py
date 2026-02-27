import os
import json
import time
from typing import List, Dict, Any
from flask import Flask, render_template, jsonify
import requests
from requests import RequestException
app = Flask(__name__)
route_info = {}
stop_info = {}


@app.route('/')
def home():
    return render_template('home.html')

@app.route('/vehicles')
def get_vehicles():
    markers = []
    fetch_data()
    with open('vehicles.json', 'r') as file:
        vehicles = json.load(file)
        for vehicle in vehicles["get_vehicles"]:
            route_color = route_info[vehicle["routeID"]]["color"]
            route_name = route_info[vehicle["routeID"]]["name"]
            marker = {
                "lat": vehicle["lat"],
                "lng": vehicle["lng"],
                "route_color": route_color,
                "route_id": vehicle["routeID"],
                "route_name": route_name,
                "equipment_id": vehicle["equipmentID"],
                "stop1": stop_info[vehicle["minutesToNextStops"][0]["stopID"]]["name"],
                "stop1_eta": vehicle["minutesToNextStops"][0]["minutes"],
                "stop2": stop_info[vehicle["minutesToNextStops"][1]["stopID"]]["name"],
                "stop2_eta": vehicle["minutesToNextStops"][1]["minutes"],
                "stop3": stop_info[vehicle["minutesToNextStops"][2]["stopID"]]["name"],
                "stop3_eta": vehicle["minutesToNextStops"][2]["minutes"],
            }
            markers.append(marker)
    return jsonify(markers)

@app.route('/announcements')
def get_announcements():
    fetch_data()
    with open('announcements.json', 'r') as file:
        announcements = json.load(file)
        return jsonify(announcements)

@app.route('/routes')
def get_routes():
    fetch_data()
    with open('routes.json', 'r') as file:
        routes = json.load(file)
        return jsonify(routes)

@app.route('/stops')
def get_stops():
    fetch_data()
    with open('stops.json', 'r') as file:
        stops = json.load(file)
        return jsonify(stops)

def fetch_data():
    if (not os.path.isfile('vehicles.json')) or (os.path.getmtime('vehicles.json') + 25) < time.time():
        vehicles = fetch_vehicles()
        with open('vehicles.json', 'w') as file:
            json.dump(vehicles, file)
        stop_etas = fetch_all_stop_etas()
        with open('stopETAs.json', 'w') as file:
            json.dump(stop_etas, file)
    if (not os.path.isfile('stops.json')) or (os.path.getmtime('stops.json') + 57600) < time.time():
        fetch_daily_data()

def fetch_daily_data():
    announcements = fetch_service_announcements()
    with open('announcements.json', 'w') as file:
        json.dump(announcements, file)
    routes = fetch_routes()
    with open('routes.json', 'w') as file:
        json.dump(routes, file)
    stops = fetch_stops()
    with open('stops.json', 'w') as file:
        json.dump(stops, file)

service_url = "https://appalcart.etaspot.net/service.php?service=get_service_announcements&token=TESTING"
vehicles_url = "https://appalcart.etaspot.net/service.php?service=get_vehicles&includeETAData=1&inService=1&orderedETAArray=1&token=TESTING"
def fetch_service_announcements():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:144.0) Gecko/20100101 Firefox/144.0",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "en-US,en;q=0.5",
        "X-Requested-With": "XMLHttpRequest",
        "Sec-GPC": "1",
    }

    try:
        response = requests.get(service_url, headers=headers)
        response.raise_for_status()
        data = response.json()

        return data

    except RequestException as e:
        print(f"An error occurred while fetching data: {e}")
        return []
    except json.JSONDecodeError:
        print("Failed to decode JSON response.")
        return []
    except ValueError as ve:
        print(ve)
        return []

def fetch_vehicles():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:144.0) Gecko/20100101 Firefox/144.0",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "en-US,en;q=0.5",
        "X-Requested-With": "XMLHttpRequest",
        "Sec-GPC": "1",
    }

    try:
        response = requests.get(vehicles_url, headers=headers)
        response.raise_for_status()
        data = response.json()

        return data

    except RequestException as e:
        print(f"An error occurred while fetching vehicle data: {e}")
        return []
    except json.JSONDecodeError:
        print("Failed to decode JSON response for vehicles.")
        return []
    except ValueError as ve:
        print(ve)
        return []

def fetch_all_stop_etas() -> List[Dict[str, Any]]:
    all_stop_etas_url = "https://appalcart.etaspot.net/service.php?service=get_stop_etas&statusData=1&token=TESTING"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:144.0) Gecko/20100101 Firefox/144.0",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "en-US,en;q=0.5",
        "X-Requested-With": "XMLHttpRequest",
        "Sec-GPC": "1",
    }

    try:
        response = requests.get(all_stop_etas_url, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data

    except RequestException as e:
        print(f"An error occurred while fetching all stop ETAs: {e}")
        return []
    except json.JSONDecodeError:
        print("Failed to decode JSON response for all stop ETAs.")
        return []
    except ValueError as ve:
        print(ve)
        return []

def fetch_routes():
    global route_info
    routes_url = "https://appalcart.etaspot.net/service.php?service=get_routes&token=TESTING"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:144.0) Gecko/20100101 Firefox/144.0",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "en-US,en;q=0.5",
        "X-Requested-With": "XMLHttpRequest",
        "Sec-GPC": "1",
    }

    try:
        response = requests.get(routes_url, headers=headers)
        response.raise_for_status()
        data = response.json()
        route_info = []
        for route in data.get("get_routes", []):
            route_info.append({
                "name": route["name"],
                "color": route["color"],
                "stops": route["stops"]
            })
        return route_info

    except RequestException as e:
        print(f"An error occurred while fetching routes: {e}")
        return []
    except json.JSONDecodeError:
        print("Failed to decode JSON response for routes.")
        return []
    except ValueError as ve:
        print(ve)
        return []

def fetch_stops():
    global stop_info
    stops_url = "https://appalcart.etaspot.net/service.php?service=get_stops&token=TESTING"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:144.0) Gecko/20100101 Firefox/144.0",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "en-US,en;q=0.5",
        "X-Requested-With": "XMLHttpRequest",
        "Sec-GPC": "1",
    }

    try:
        response = requests.get(stops_url, headers=headers)
        response.raise_for_status()
        data = response.json()
        stop_info = []

        for stop in data.get("get_stops", []):
            stop_info.append({
                "name": stop["name"],
                "lat": stop["lat"],
                "lng": stop["lng"]
            })

        return stop_info

    except RequestException as e:
        print(f"An error occurred while fetching stops: {e}")
        return []
    except json.JSONDecodeError:
        print("Failed to decode JSON response for stops.")
        return []
    except ValueError as ve:
        print(ve)
        return []

if __name__ == "__main__":
    # Railway provides a PORT environment variable automatically
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
    fetch_data()
    with open('routes.json', 'r') as file:
        route_info = json.load(file)
    with open('stops.json', 'r') as file:
        stop_info = json.load(file)
