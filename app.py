import os
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "<h1>Hello from Flask on Railway!</h1>"

if __name__ == "__main__":
    # Railway provides a PORT environment variable automatically
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
