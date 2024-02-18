from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, FileField
from wtforms.validators import InputRequired, EqualTo, Regexp

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
    recipe_name = StringField('Title:', validators=[InputRequired()])
    ingredients = StringField('Ingredients:', validators=[InputRequired()]) #can I make it like a list??????
    steps = StringField('Steps:', validators=[InputRequired()]) #can I make it like a list??????

    UPLOAD_FOLDER = '/static/'
    ALLOWED_EXTENSIONS = ['png', 'jpg', 'jpeg']
    image = FileField('Upload Image') # potentially more images 
    submit = SubmitField('Publish')