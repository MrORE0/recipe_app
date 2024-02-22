from flask import Flask, render_template, redirect, make_response, request, url_for
from database import get_db, close_db 
from forms import RegistrationForm, LoginForm, UploadForm
import os
#hashing the password including salting
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config ["SECRET_KEY"] = "this-is-my-secret-key"
app.config['UPLOAD_FOLDER'] = 'static/'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    app.config['UPLOAD_FOLDER'] = 'static/'
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
    return render_template('register.html', form = form, notGuest = False)

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
    return render_template('login.html', form = form, notGuest = False)

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
            type = form.type.data
            allergies = form.allergies.data
            steps = form.steps.data
            username = request.cookies.get('username')
            db = get_db() 
            db.execute(
                """INSERT INTO recipes (username, title, ingredients, steps, image_path, allergies, type)
                VALUES (?, ?, ?, ?, ?, ?, ?);""",
                (username, title, ingredients, steps, image_path.strip('/static'), allergies, type)
            )
            db.commit()
            return redirect('/home')
        else:
            return 'Invalid file format'
    return render_template('recipe_upload.html', form=form)

@app.route('/edit/<id>', methods=['GET', 'POST'])
def edit(id):
    db = get_db()
    recipe = db.execute("SELECT * FROM recipes WHERE id = ?", (id,)).fetchone()
    if not recipe:
        return "Recipe not found", 404

    form = UploadForm(obj=recipe)  # Pass recipe object to populate form fields

    if form.validate_on_submit():
        file = request.files['file']
        if file:
            if allowed_file(file.filename):
                filename = secure_filename(file.filename)
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

                # Remove old image if it exists
                if recipe['image_path']:
                    os.remove(url_for('static', filename=recipe['image_path']))

                image_path_db = image_path.strip('/static')
            else:
                return 'Invalid file format'
        else:
            image_path_db = recipe['image_path']

        title = form.title.data
        ingredients = form.ingredients.data
        steps = form.steps.data
        allergies = form.allergies.data
        type = form.type.data
        username = request.cookies.get('username')

        db.execute(
            """UPDATE recipes
                SET username = ?, title = ?, ingredients = ?, steps = ?, image_path = ?, allergies = ?, type = ?
                WHERE id = ?""",
            (username, title, ingredients, steps, image_path_db, allergies, type, id)
        )
        db.commit()
    
        # If an exception occurs during commit, rollback the deletion of the new image
        if file:
            os.remove(image_path) #no need to delete the old picture (your need permissions)
        return render_template('recipe_upload.html', form=form)

        # Fetch the updated recipe from the database
        updated_recipe = db.execute("SELECT * FROM recipes WHERE id = ?", (id,)).fetchone()
        if not updated_recipe:
            return render_template('recipe_upload.html', form=form)
        else:
            return redirect('/open_recipe/', id=id)

    # Populate form fields with existing recipe data
    form.title.data = recipe['title']
    form.ingredients.data = recipe['ingredients']
    form.steps.data = recipe['steps']
    form.allergies.data = recipe['allergies']
    form.type.data = recipe['type']
    username = request.cookies.get('username')
    return render_template('recipe_upload.html', form=form)

@app.route('/', methods = ['GET', 'POST'])
@app.route('/home', methods = ['GET', 'POST'])
def home():
    db = get_db()
    recipes = db.execute(
        """SELECT * FROM recipes;""").fetchall()
    return render_template('index.html', recipes = recipes)

@app.route('/open_recipe/<id>', methods = ['GET', 'POST'])
def open_recipe(id):
    form = UploadForm()
    username = request.cookies.get('username')
    db = get_db()
    publisher = db.execute("""
        SELECT users.username AS username
        FROM recipes
        JOIN users ON recipes.username = users.username
        WHERE recipes.id = ?;""", (id,)).fetchone()
    if publisher['username'] == username:
        recipe = db.execute("SELECT * FROM recipes WHERE id = ?",(id,)).fetchone()
        return render_template('open_recipe.html', recipe = recipe, publisher=True, form=form)
    else:
        recipe = db.execute("SELECT * FROM recipes WHERE id = ?",(id,)).fetchone()
        return render_template('open_recipe.html', recipe = recipe, publisher=False, form=form)