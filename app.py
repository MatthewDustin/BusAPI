import os
import json
from flask import Flask

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
    import requests
    response = requests.get('https://api.example.com/data')
    data = response.json()
    # save data to file
    with open('data.json', 'w') as file:
        json.dump(data, file)

if __name__ == "__main__":
    # Railway provides a PORT environment variable automatically
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
