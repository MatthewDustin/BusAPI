import os
import json

import requests
from requests import RequestException

from app import fetch_data

if __name__ == "__main__":
    with open('data.json', 'r') as file:
        data = json.load(file)
        print(data)
        for vehicle in data["get_vehicles"]:
            print(vehicle["lat"])



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