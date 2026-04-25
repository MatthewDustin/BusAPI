import os, json, time, logging
from typing import List, Dict, Any
from requests import RequestException
import requests

routes = {}
stops = {}
service_url = "https://appalcart.etaspot.net/service.php?service=get_service_announcements&token=TESTING"
vehicles_url = "https://appalcart.etaspot.net/service.php?service=get_vehicles&includeETAData=1&inService=1&orderedETAArray=1&token=TESTING"

def fetch_data(app=None):
    global routes, stops
    if (not os.path.isfile('stops.json')) or (not os.path.isfile('routes.json')) or (not os.path.isfile('announcements.json')) or (os.path.getmtime('stops.json') + 57600) < time.time():
        fetch_daily_data()
    if (not os.path.isfile('vehicles.json')) or (os.path.getmtime('vehicles.json') + 12) < time.time():
        vehicles = fetch_vehicles()
        with open('vehicles.json', 'w') as file:
            json.dump(vehicles, file)
        stop_etas = fetch_all_stop_etas()
        with open('stopETAs.json', 'w') as file:
            json.dump(stop_etas, file)
    try:
        with open('routes.json', 'r') as file:
            routes = json.load(file)
    except (json.JSONDecodeError, FileNotFoundError):
        routes = {}
    try:
        with open('stops.json', 'r') as file:
            stops = json.load(file)
    except (json.JSONDecodeError, FileNotFoundError):
        stops = {}
    update_clean(app)

def update_clean(app=None):
    global stops, routes

    try:
        with open('stops.json', 'r') as file:
            stops = json.load(file)
    except (json.JSONDecodeError, FileNotFoundError):
        stops = {}
    try:
        with open('routes.json', 'r') as file:
            routes = json.load(file)
    except (json.JSONDecodeError, FileNotFoundError):
        routes = {}
    for stop in stops.keys():
        stops[str(stop)]['routes'] = []
    for route in routes.keys():
        route = str(route)
        routes[route]['stopNames'] = []
        for stop in routes[route]["stopIDs"]:
            stop = str(stop)
            if stop in stops.keys():
                routes[route]['stopNames'].append(stops[stop]['name'])
                if routes[route]["name"] not in stops[stop]["routes"]:
                    stops[stop]["routes"].append(routes[route]["name"])
    with open('routes.json', 'w') as file:
        json.dump(routes, file)
    try:
        with open('stopETAs.json', 'r') as eta_file:
            stop_etas = json.load(eta_file)
    except (json.JSONDecodeError, FileNotFoundError):
        stop_etas = {"get_stop_etas": []}
    for stop in stop_etas["get_stop_etas"]:
        stop_id = str(stop["id"])
        if stop_id in stops.keys():
            etas = []
            nextBuses = []
            for bus in stop["enRoute"]:
                etas.append(bus['minutes'])
                nextBuses.append(bus['equipmentID'])
            stops[stop_id]["etas"] = etas
            stops[stop_id]["nextBuses"] = nextBuses
    with open('stops.json', 'w') as file:
        json.dump(stops, file)

    buses = []

    if app:
        app.logger.info(f"Loaded routes: {list(routes.keys())}")
    try:
        with open('vehicles.json', 'r') as file:
            vehicles = json.load(file)
    except (json.JSONDecodeError, FileNotFoundError):
        vehicles = {"get_vehicles": []}

    for vehicle in vehicles["get_vehicles"]:
        stopNames = []
        etas = []
        for stop in vehicle["minutesToNextStops"]:
            if str(stop["stopID"]) in stops.keys():
                stopNames.append(stops[str(stop["stopID"])]["name"])
                etas.append(stop["minutes"])
        route_id = str(vehicle["routeID"])
        buses.append({
            "name": vehicle["equipmentID"],
            "lat": vehicle["lat"],
            "lng": vehicle["lng"],
            "routeID": vehicle["routeID"],
            "route": routes[route_id]["name"] if route_id in routes else "Unknown",
            "inService": vehicle["inService"] == 1,
            "load": vehicle["load"],
            "onSchedule": vehicle["onSchedule"],
            "stops": stopNames,
            "etas": etas
        })
    with open('buses.json', 'w') as file:
        json.dump(buses, file)

def fetch_daily_data():
    global stops, routes
    announcements = fetch_service_announcements()
    with open('announcements.json', 'w') as file:
        json.dump(announcements, file)
    routes = fetch_routes()
    with open('routes.json', 'w') as file:
        json.dump(routes, file)
    stops = fetch_stops()
    with open('stops.json', 'w') as file:
        json.dump(stops, file)

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

def fetch_routes(app=None):
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
            if app:
                app.logger.info(f"Processing route: {route['name']} with ID: {route['id']}")
            routes[route["id"]] = {
                "name": route["name"],
                "color": route["color"],
                "stopIDs": route["stops"],
                "encodedLine": route["encLine"],
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
