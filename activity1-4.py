from flask import Flask, render_template, session, redirect, url_for, flash # Import flask, the template renderer, and session/redirect/flash helpers
from flask_bootstrap import Bootstrap # Bootstrap styling (navbar, layout)
from flask_moment import Moment # Render dates/times in the user's local time zone
from flask_wtf import FlaskForm # Base class for web forms (with CSRF protection)
from wtforms import StringField, SubmitField # Form fields
from wtforms.validators import DataRequired, ValidationError # Validator that rejects empty input, and the error custom validators raise

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
        return redirect(url_for('index')) # Post/Redirect/Get so refreshing doesn't resubmit
    return render_template('name_form.html', form=form, name=session.get('name'), email=session.get('email'))
