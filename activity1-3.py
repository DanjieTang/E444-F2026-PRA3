from datetime import datetime, timezone
from flask import Flask, render_template # Import flask and the template renderer
from flask_bootstrap import Bootstrap # Bootstrap styling (navbar, layout)
from flask_moment import Moment # Render dates/times in the user's local time zone

app = Flask(__name__) # Setup for flask
bootstrap = Bootstrap(app) # Attach Bootstrap to the app
moment = Moment(app) # Attach Moment to the app

@app.route('/') # Home page
def index():
    return render_template('index.html', current_time=datetime.now(timezone.utc)) # Pass the current UTC time to the template

@app.route('/user/<name>') # A route that asks for a path parameter
def user(name):
    return render_template('user.html', name=name, current_time=datetime.now(timezone.utc)) # Greet the user by name and show the time
