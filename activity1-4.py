import os # Read the API key from environment variables
import time # Wait between retries when the API is rate limited
import requests # HTTP client for calling the OpenRouter API
from dotenv import load_dotenv # Load variables from the .env file into the environment
from flask import Flask, render_template, session, redirect, url_for, flash, request # Import flask, the template renderer, session/redirect/flash helpers, and the incoming request
from flask_bootstrap import Bootstrap # Bootstrap styling (navbar, layout)
from flask_moment import Moment # Render dates/times in the user's local time zone
from flask_wtf import FlaskForm # Base class for web forms (with CSRF protection)
from wtforms import StringField, SubmitField # Form fields
from wtforms.validators import DataRequired, ValidationError # Validator that rejects empty input, and the error custom validators raise

load_dotenv() # Makes OPEN_ROUTER_API_KEY from .env available through os.environ

OPENROUTER_URL = 'https://openrouter.ai/api/v1/chat/completions' # OpenAI-compatible chat endpoint
OPENROUTER_MODEL = os.environ.get('OPEN_ROUTER_MODEL', 'qwen/qwen3.8-flash') # Any model id from openrouter.ai/models
MAX_HISTORY = 10 # Only keep the last few messages, since the session cookie is limited to about 4 KB
MAX_RETRIES = 2 # Extra attempts when OpenRouter or the model provider is temporarily busy
RETRY_STATUSES = {429, 502, 503} # Rate limited, or the upstream provider is down/overloaded

app = Flask(__name__) # Setup for flask
app.config['SECRET_KEY'] = 'hard to guess string' # Needed for sessions and CSRF tokens
bootstrap = Bootstrap(app) # Attach Bootstrap to the app
moment = Moment(app) # Attach Moment to the app

def uoft_email(form, field): # Custom validator: must contain an '@' and be a UofT address
    if '@' not in field.data:
        raise ValidationError(f"Please include an '@' in the email address. '{field.data}' is missing an '@'.")
    if 'utoronto' not in field.data:
        raise ValidationError('Please use your UofT email.')

class NameForm(FlaskForm): # A form with name and email text fields and a submit button
    name = StringField('What is your name?', validators=[DataRequired()])
    email = StringField('What is your UofT Email address?', validators=[DataRequired(), uoft_email])
    submit = SubmitField('Submit')

@app.route('/', methods=['GET', 'POST']) # Home page, accepts form submissions
def index():
    form = NameForm()
    if form.validate_on_submit(): # True only on a valid POST
        old_name = session.get('name')
        if old_name is not None and old_name != form.name.data:
            flash('Looks like you have changed your name!') # Show an alert when the name changes
        old_email = session.get('email')
        if old_email is not None and old_email != form.email.data:
            flash('Looks like you have changed your email!') # Show an alert when the email changes
        session['name'] = form.name.data # Remember the name across requests
        session['email'] = form.email.data # Remember the email across requests
        return redirect(url_for('chatbot')) # Post/Redirect/Get to the chatbot page so refreshing doesn't resubmit
    return render_template('name_form.html', form=form, name=session.get('name'), email=session.get('email'))

@app.route('/chatbot') # Chatbot page, only reachable after submitting the form
def chatbot():
    if session.get('name') is None: # No name in the session yet, so send the user to the form first
        return redirect(url_for('index'))
    return render_template('chat.html', name=session.get('name'))

@app.route('/chat', methods=['POST']) # Receives one chat message as JSON and returns the bot's reply
def chat():
    message = request.json['message'].strip()
    history = session.get('history', []) # Earlier messages, e.g. [{'role': 'user', 'content': 'My name is Alice.'}, ...]
    history.append({'role': 'user', 'content': message})
    system = {'role': 'system', 'content': f"You are Flasky, a friendly chatbot. The user's name is {session.get('name')}. Keep replies short."}
    try:
        for attempt in range(MAX_RETRIES + 1):
            response = requests.post(
                OPENROUTER_URL,
                headers={'Authorization': f"Bearer {os.environ['OPEN_ROUTER_API_KEY']}"},
                json={'model': OPENROUTER_MODEL, 'messages': [system] + history},
                timeout=60,
            )
            if response.status_code not in RETRY_STATUSES or attempt == MAX_RETRIES:
                break
            time.sleep(min(float(response.headers.get('Retry-After', 2 ** attempt)), 10)) # Wait 1s, 2s, ... (or what the server asks) before trying again
        if not response.ok: # OpenRouter explains the problem in the body, e.g. {"error": {"message": "... rate-limited upstream ..."}}
            try:
                detail = response.json()['error']['message']
            except (ValueError, KeyError):
                detail = response.text[:200]
            app.logger.warning('OpenRouter error %s: %s', response.status_code, response.text)
            return {'reply': f'Sorry, the chatbot service returned an error ({response.status_code}: {detail}). Please try again.'}
        reply = response.json()['choices'][0]['message']['content']
    except KeyError: # OPEN_ROUTER_API_KEY is missing, or the response had an unexpected shape
        return {'reply': 'The chatbot is not configured correctly. Is OPEN_ROUTER_API_KEY set in .env?'}
    except requests.RequestException as error: # Network problem or timeout
        return {'reply': f'Sorry, I could not reach the chatbot service ({error}).'}
    history.append({'role': 'assistant', 'content': reply})
    session['history'] = history[-MAX_HISTORY:] # Reassign so Flask notices the change and saves the cookie
    return {'reply': reply}

@app.route('/logout', methods=['POST']) # Forget everything stored for this user and go back Home
def logout():
    session.clear() # Removes the name, email, and chat history from the session
    flash('You have been logged out.')
    return redirect(url_for('index'))
