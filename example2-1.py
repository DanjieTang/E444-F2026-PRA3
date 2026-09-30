from flask import Flask # Import the flask library
app = Flask(__name__) # Setup for flask

@app.route('/') # Create a new route
def index():
    return '<h1>Hello World!</h1>' # Return HTML of h1 of hello world

@app.route('/user/<name>') # A new route that asks for a path parameter
def user(name):
    return '<h1>Hello, {}!</h1>'.format(name) # Return HTML with h1 of hello and then user name