from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, DecimalField, SelectField, SelectMultipleField, widgets
from wtforms.validators import InputRequired, EqualTo, Regexp, NumberRange

class RegistrationForm(FlaskForm):
    username = StringField('Username:', validators=[InputRequired(),Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
                                                                            'Usernames must have only letters, numbers, underscores or dots')])
    #got the regexp from GPT 
    password = PasswordField('Password:', validators=[InputRequired()])
    """, Regexp(
            r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$',
            message="Password must be at least 8 characters long and contain at least one uppercase letter, one lowercase letter, one digit, and one special character."
        )])"""
    #keep in minds that in password2 the equalto string is referencing the value of the password variable
    password2 = PasswordField('Confirm password:', validators=[InputRequired(), EqualTo('password', message='Passwords must match.')])
    submit = SubmitField('Register')
    
class LoginForm(FlaskForm):
    username = StringField('Username:', validators=[InputRequired()])
    password = PasswordField('Password:', validators=[InputRequired()])
    submit = SubmitField('Login')
    #try to add a cookie for remembering option (linking it to a profile)
    
class UploadForm(FlaskForm):
    title = StringField('Title:', validators=[InputRequired()])
    ingredients = StringField('Ingredients:', validators=[InputRequired()]) #can I make it like a list??????
    steps = StringField('Steps:', validators=[InputRequired()], render_kw={"rows": 5}) #can I make it like a list??????
    type = SelectField('Type(breakfast, lunch, dinner, snack):', choices=['Breakfast', 'Lunch', 'Dinner', 'Snack'], default='Breakfast')
    allergies = StringField('Allergies:')
    submit = SubmitField('Publish')
    edit = SubmitField('Edit')
    delete = SubmitField('Delete')

class ReviewForm(FlaskForm):
    feedback = StringField('Feedback:', validators=[InputRequired()])
    score = DecimalField('Score', validators=[InputRequired(), NumberRange(1,5)])
    submit = SubmitField('Comment')

class Filters(FlaskForm):
    type_filters = [('Breakfast', 'breakfast'), ('Lunch', 'Lunch'), ('Dinner', 'dinner'), ('Snack', 'snack')]
    #this is usually a dropdown menu, but with the option_widget we render it as checkboxes that can be selected
    type_checkboxes = SelectMultipleField('Type:', choices=type_filters, option_widget=widgets.CheckboxInput())