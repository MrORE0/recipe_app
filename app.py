from flask import Flask, render_template, redirect, make_response, request, url_for, g, session, flash
from database import get_db, close_db 
from forms import RegistrationForm, LoginForm, UploadForm, Filters
from functools import wraps
import os
#hashing the password including salting
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config ["SECRET_KEY"] = "this-is-my-secret-key"
app.config['UPLOAD_FOLDER'] = 'static/'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg'}
app.teardown_appcontext(close_db)

# login required functions
@app.before_request
def load_logged_in_user():
#this will run before each request and will get the username in a g(global).variable(user)
    g.user = session.get('username', None) 

#here we define a route (@login_required)
def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if g.user is None:
            return redirect(url_for('login', next=request.url))
        return view(*args, **kwargs)
    return wrapped_view

def allowed_file(filename):
    app.config['UPLOAD_FOLDER'] = 'static/'
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']



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
        username = form.username.data.strip(' ')
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
                session.clear()
                session['username'] = username
                next_page = request.args.get('next')
                if not next_page:
                    next_page = url_for('home')
                response = make_response(redirect(next_page))
                response.set_cookie('username', username)
                return response
            else:
                #add cookies here   
                return render_template('login.html', message = 'Invalid Username or Password. Please check your username and try again.', form = form)
    return render_template('login.html', form = form, notGuest = False)

@app.route('/logout', methods = ['GET', 'POST'])
def logout():
    session.clear()
    return redirect(url_for('home'))


#function for checking when uploading/editing recipe
def process_recipe_form(recipe):
    form = UploadForm()
    if form.validate_on_submit():
        file = request.files['file']
        if file:
            if allowed_file(file.filename):
                filename = secure_filename(file.filename)
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(image_path)
                image_path_db = image_path.strip('/static')
            else:
                return 'Invalid file format'
        else:
            if recipe is not None:
                image_path_db = recipe['image_path']
            else:
                image_path_db = None

        db = get_db()
        if recipe is None:
            db.execute(
                """INSERT INTO recipes (username, title, ingredients, steps, image_path, allergies, type)
                VALUES (?, ?, ?, ?, ?, ?, ?);""",
                (g.user, form.title.data, form.ingredients.data, form.steps.data, image_path_db, form.allergies.data, form.type.data)
            )
        else:
            db.execute(
                """UPDATE recipes
                SET username = ?, title = ?, ingredients = ?, steps = ?, image_path = ?, allergies = ?, type = ?
                WHERE id = ?;""",
                (g.user, form.title.data, form.ingredients.data, form.steps.data, image_path_db, form.allergies.data, form.type.data, recipe['id'])
            )
        db.commit()
        return True
    return False

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    form = UploadForm()
    if process_recipe_form(None):
        return redirect('/home')
    return render_template('recipe_upload.html', form=form)


@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    db = get_db()
    recipe = db.execute("SELECT * FROM recipes WHERE id = ?", (id,)).fetchone()
    if not recipe:
        return "Recipe not found", 404
    
    form = UploadForm()
    form.title.data = recipe['title']
    form.ingredients.data = recipe['ingredients']
    form.steps.data = recipe['steps']
    form.allergies.data = recipe['allergies']
    form.type.data = recipe['type']

    if process_recipe_form(recipe):
        return redirect(url_for('open_recipe', id=id))
    return render_template('recipe_upload.html', form=form)

@app.route('/delete/<int:id>', methods=['GET', 'POST'])
@login_required
def delete(id):
    db = get_db()
    db.execute("""DELETE FROM recipes WHERE id = ?;""",(id,))
    db.commit()
    flash('You successfully deleted this recipe.')
    return redirect(url_for('home'))

@app.route('/favourite/<int:id>', methods=['GET', 'POST'])
@login_required
def favourite(id):
    db = get_db()
    isFavourite = db.execute("SELECT * FROM favourites WHERE recipe_id = ? AND username = ?;", (id, g.user)).fetchone()
    if isFavourite: #it is already fav, so when clicked it becomes not favourite
        db.execute("""DELETE FROM favourites WHERE recipe_id = ? AND username = ?;""",(id, g.user))
        db.commit()
        flash('You have removed this recipe from favourites.')
    else:
        db.execute("""INSERT INTO favourites(recipe_id, username)
                   VALUES (?,?);""",(id, g.user))
        db.commit()
        flash("You have added this recipe to favourites.")
    return redirect(url_for('open_recipe', id = id))

@app.route('/open_favourites/<username>', methods=['GET', 'POST'])
@login_required
def open_favourites(username):
    form = Filters()
    db = get_db()
    recipes = db.execute(
        """SELECT * FROM recipes
        WHERE id in (
            SELECT recipe_id FROM favourites
            WHERE username = ?
        );""", (g.user,)).fetchall()
    if form.validate_on_submit(): #this part doesn't work properly!!!!!!!!!!!!!!!!
        filters.append(form.type_checkboxes.data)
        if g.user:
            return render_template('index.html', recipes = recipes, notGuest = True, form=form, message = filters)
        else:
            return render_template('index.html', recipes = recipes, notGuest = False, form=form, message = filters)
    if g.user:
        return render_template('index.html', recipes = recipes, notGuest = True, form=form, message = filters)    
    else:
        return render_template('index.html', recipes = recipes, notGuest = False, form=form, message = filters)
     

@app.route('/open_my_recipes/<username>', methods=['GET', 'POST'])
@login_required
def open_my_recipes(username):
    form = Filters()
    db = get_db()
    recipes = db.execute(
        """SELECT * FROM recipes
        WHERE username = ? ;""", (g.user,)).fetchall()
    if form.validate_on_submit(): #this part doesn't work properly!!!!!!!!!!!!!!!!
        filters.append(form.type_checkboxes.data)
        if g.user:
            return render_template('index.html', recipes = recipes, notGuest = True, form=form, message = filters)
        else:
            return render_template('index.html', recipes = recipes, notGuest = False, form=form, message = filters)
    if g.user:
        return render_template('index.html', recipes = recipes, notGuest = True, form=form, message = filters)    
    else:
        return render_template('index.html', recipes = recipes, notGuest = False, form=form, message = filters)
    

#here we check the filters and execute searches based on them
def checkFilters():
    return

filters = []
@app.route('/', methods = ['GET', 'POST'])
@app.route('/home', methods = ['GET', 'POST'])
def home():
    form = Filters()
    db = get_db()
    recipes = db.execute(
        """SELECT * FROM recipes;""").fetchall()
    if form.validate_on_submit(): #this part doesn't work properly!!!!!!!!!!!!!!!!
        filters.append(form.type_checkboxes.data)
        if g.user:
            return render_template('index.html', recipes = recipes, notGuest = True, form=form, message = filters)
        else:
            return render_template('index.html', recipes = recipes, notGuest = False, form=form, message = filters)
    if g.user:
        return render_template('index.html', recipes = recipes, notGuest = True, form=form, message = filters)    
    else:
        return render_template('index.html', recipes = recipes, notGuest = False, form=form, message = filters)
     
@app.route('/open_recipe/<int:id>', methods=['GET', 'POST'])
def open_recipe(id):
    form = UploadForm()
    db = get_db()
    
    publisher = db.execute("""
        SELECT users.username AS username
        FROM recipes
        JOIN users ON recipes.username = users.username
        WHERE recipes.id = ?;
        """, (id,)).fetchone()
    
    favourite = db.execute("""
        SELECT f.username AS username FROM recipes as r
        JOIN favourites AS f ON r.id = f.recipe_id
        JOIN users AS u ON f.username = u.username
        WHERE id = ?;""", (id,)).fetchall()
    
    if favourite:
        for users in favourite:
            if g.user in users['username']:
                filename = 'star_full.png'
            else:
                filename = 'star_empty.png'
    else:
        filename = 'star_empty.png'

    if publisher and publisher['username'] is not None:
        if publisher['username'] == g.user or g.user == 'admin':
            notGuest = True if g.user else False
            recipe = db.execute("SELECT * FROM recipes WHERE id = ?", (id,)).fetchone()
            return render_template('open_recipe.html', recipe=recipe, publisher=True, form=form, notGuest=notGuest, filename=filename)
        else:
            notGuest = True if g.user else False
            recipe = db.execute("SELECT * FROM recipes WHERE id = ?", (id,)).fetchone()
            return render_template('open_recipe.html', recipe=recipe, publisher=False, form=form, notGuest=notGuest,filename = filename)
    else:
        return "Publisher not found", 404

