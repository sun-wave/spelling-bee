import os
from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return "Hello from Flask!"

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080)) # Default to 8080 if PORT not set
    app.run(host='0.0.0.0', port=port)
