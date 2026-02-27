import os
import json
import time
from typing import List, Dict, Any
from flask import Flask, render_template, jsonify
import requests
from requests import RequestException
app = Flask(__name__)
routes = {}
stops = {}

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/vehicles')
def get_vehicles():
    global routes, stops
    markers = []
    fetch_data()
    with open('vehicles.json', 'r') as file:
        vehicles = json.load(file)
        for vehicle in vehicles["get_vehicles"]:
            route_color = routes[vehicle["routeID"]]["color"]
            route_name = routes[vehicle["routeID"]]["name"]
            marker = {
                "lat": vehicle["lat"],
                "lng": vehicle["lng"],
                "route_color": route_color,
                "route_id": vehicle["routeID"],
                "route_name": route_name,
                "equipment_id": vehicle["equipmentID"],
                "stop1": stops[vehicle["minutesToNextStops"][0]["stopID"]]["name"],
                "stop1_eta": vehicle["minutesToNextStops"][0]["minutes"],
                "stop2": stops[vehicle["minutesToNextStops"][1]["stopID"]]["name"],
                "stop2_eta": vehicle["minutesToNextStops"][1]["minutes"],
                "stop3": stops[vehicle["minutesToNextStops"][2]["stopID"]]["name"],
                "stop3_eta": vehicle["minutesToNextStops"][2]["minutes"],
            }
            markers.append(marker)
    return jsonify(markers)

@app.route('/announcements')
def get_announcements():
    fetch_data()
    with open('announcements.json', 'r') as file:
        announcements = json.load(file)
        announcements['file_age'] = time.time() - os.path.getmtime('announcements.json')
        return jsonify(announcements)

@app.route('/routes')
def get_routes():
    fetch_data()
    with open('routes.json', 'r') as file:
        routes = json.load(file)
        return jsonify(routes.values())

@app.route('/stops')
def get_stops():
    fetch_data()
    with open('stops.json', 'r') as file:
        stops = json.load(file)
        return jsonify(stops.values())

@app.route('/buses')
def get_buses():
    fetch_data()
    with open('vehicles.json', 'r') as file:
        vehicles = json.load(file)
        return jsonify(vehicles)

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
    update_clean()

def update_clean():
    global stops, routes
    for stop in stops.keys():
        stops[stop]['routes'] = []
    for route in routes.keys():
        routes[route]['stopNames'] = []
        for stop in routes[route]["stopIDs"]:
            if stop in stops.keys():
                routes[route]['stopNames'].append(stops[stop]['name'])
                if routes[route]["name"] not in stops[stop]["routes"]:
                    stops[stop]["routes"].append(routes[route]["name"])
    with open('routes.json', 'w') as file:
        json.dump(routes, file)
    with open('stopETAs.json', 'r') as eta_file:
        stop_etas = json.load(eta_file)
        for stop in stop_etas["get_stop_etas"]:
            if stop["id"] in stops.keys():
                etas = []
                nextBuses = []
                for bus in stop["enRoute"]:
                    etas.append(bus['minutes'])
                    nextBuses.append(bus['equipmentID'])
                stops[stop["id"]]["etas"] = etas
                stops[stop["id"]]["nextBuses"] = nextBuses
    with open('stops.json', 'w') as file:
        json.dump(stops, file)

    buses = []
    with open('vehicles.json', 'r') as file:
        vehicles = json.load(file)

        for vehicle in vehicles["get_vehicles"]:
            stopNames = []
            etas = []
            for stop in vehicle["minutesToNextStops"]:
                if stop["stopID"] in stops.keys():
                    stopNames.append(stops[stop["stopID"]]["name"])
                    etas.append(stop["minutes"])
            buses.append({
                "name": vehicle["equipmentID"],
                "lat": vehicle["lat"],
                "lng": vehicle["lng"],
                "routeID": vehicle["routeID"],
                "route": routes[vehicle["routeID"]]["name"],
                "inService": vehicle["inService"],
                "load": vehicle["load"],
                "onSchedule": vehicle["onSchedule"],
                "stops": stopNames,
                "etas": etas
            })
    with open('vehicles.json', 'w') as file:
        json.dump(buses, file)
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
    global routes
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
        routes = {}
        for route in data.get("get_routes", []):
            routes[route["id"]] = {
                "name": route["name"],
                "color": route["color"],
                "stopIDs": route["stops"],
                "stopNames": []
            }
        return routes

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
    global stops
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
        stops = {}
        for stop in data.get("get_stops", []):
            stops[stop["id"]] = {
                "name": stop["name"],
                "lat": stop["lat"],
                "lng": stop["lng"],
                "routes": [],
                "etas": [],
                "nextBuses": []
            }

        return stops

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
