from flask import Flask, render_template, redirect, make_response, request
from database import get_db, close_db 
from forms import RegistrationForm, LoginForm, UploadForm
import os
#hashing the password including salting
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app. config ["SECRET_KEY"] = "this-is-my-secret-key"
app.config['UPLOAD_FOLDER'] = 'static/'
def allowed_file(filename):
    app.config['UPLOAD_FOLDER'] = 'static/'
    app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

app.teardown_appcontext(close_db)


@app.route('/register', methods = ['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        #no need for password 2 if its already validated
        db = get_db()
        conflict_user = db.execute(
            """SELECT * FROM users
            WHERE username = ?;""", (username,)).fetchone()
        if conflict_user is not None:
            form.username.errors.append('User name already taken.')
        else:
            db.execute(
                """INSERT INTO users (username, password)
                VALUES (?, ?);""", (username, generate_password_hash(password)))
            db.commit()
            return redirect('/login')
    return render_template('register.html', form = form)

@app.route('/login', methods = ['GET', 'POST'])
def login():
    form = LoginForm() 
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        db = get_db()
        registered_user = db.execute(
        """SELECT * FROM users
        WHERE username = ?;""", (username,)).fetchone()
        if registered_user is None:
    # User not found
            return render_template('login.html', message = 'Invalid Username or Password. Please check your username and try again.', form = form)
        else:
            hashed_password = registered_user['password']
            if check_password_hash(hashed_password, password):
                response = make_response(redirect('/home'))
                response.set_cookie('username', username)
                return response
            else:
                #add cookies here   
                return render_template('login.html', message = 'Invalid Username or Password. Please check your username and try again.', form = form)
    return render_template('login.html', form = form)

@app.route('/upload', methods = ['GET', 'POST'])
def upload():
    form = UploadForm()  # Creating an instance of the UploadForm class
    if form.validate_on_submit():
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(image_path)  # Saving the file with the correct filename
            title = form.title.data
            ingredients = form.ingredients.data
            steps = form.steps.data
            username = request.cookies.get('username')
            db = get_db() 
            db.execute(
                """INSERT INTO recipes (username, title, ingredients, steps, image_path)
                VALUES (?, ?, ?, ?, ?);""",
                (username, title, ingredients, steps, image_path.strip('/static'))
            )
            db.commit()
            return render_template('recipe_upload.html', form=form)
        else:
            return 'Invalid file format'
    return render_template('recipe_upload.html', form=form)

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    db = get_db()
    recipe = db.execute(
        "SELECT * FROM recipes WHERE id = ?",
        (id,)
    ).fetchone()

    if not recipe:
        return "Recipe not found", 404

    form = UploadForm()  # Creating an instance of the UploadForm class
    if form.validate_on_submit():
        title = form.title.data
        ingredients = form.ingredients.data
        steps = form.steps.data
        username = request.cookies.get('username')

        file = request.files['file']
        if file and allowed_file(file.filename):
            # If a new image is uploaded, delete the old image file
            if recipe['image_path']:
                os.remove(recipe['image_path'])

            filename = secure_filename(file.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(image_path)  # Saving the new file with the correct filename

            db.execute(
                """UPDATE recipes
                SET title = ?, ingredients = ?, steps = ?, image_path = ?
                WHERE id = ?""",
                (title, ingredients, steps, image_path, id)
            )
            db.commit()

            return 'done' #redirect('recipe_detail', id=id)
        else:
            return 'Invalid file format'





@app.route('/', methods = ['GET', 'POST'])
@app.route('/home', methods = ['GET', 'POST'])
def home():

    db = get_db()
    recipes = db.execute(
        """SELECT * FROM recipes;""").fetchall()
    return render_template('index.html', recipes = recipes)