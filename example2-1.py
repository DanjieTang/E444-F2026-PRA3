from flask import Flask # Import the flask library
app = Flask(__name__) # Setup for flask

@app.route('/') # Create a new route
def index():
    return '<h1>Hello World!</h1>' # Return HTML of h1 of hello world