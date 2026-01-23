import os
import json
from flask import Flask
import requests
from requests import RequestException

app = Flask(__name__)

@app.route('/')
def home():
    return "<h1>Hello from Flask on Railway!</h1>"

@app.route('/api', methods=['GET'])
def api():
    # check if file already exists
    if os.path.isfile('data.json'):
        # check if file is at most 1 day old
        if (os.path.getmtime('data.json') + 86400) > os.path.getmtime('data.json'):
            with open('data.json', 'r') as file:
                data = json.load(file)
                return data
    fetch_data()
    with open('data.json', 'r') as file:
        data = json.load(file)
        return data

def fetch_data():
    # request data from external API

    data = fetch_vehicles()
    # save data to file
    with open('data.json', 'w') as file:
        json.dump(data, file)

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

if __name__ == "__main__":
    # Railway provides a PORT environment variable automatically
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
