"""
When uploading a picture is always required however whats not true for the edit there you can keep the already uploaded one
Only the admin or the user who commented can delete a comment
Users:
username    password
admin        admin321
mert         123
nikol        321
"""


from flask import Flask, render_template, redirect, make_response, request, url_for, g, session, flash
from database import get_db, close_db 
from forms import RegistrationForm, LoginForm, UploadForm, Filters, ReviewForm
from functools import wraps
import os
import re
import uuid
from random import choice
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
            return redirect('login')
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
                filename_parts = filename.split('.')
                filename_parts[0] = str(uuid.uuid4())
                filename = '.'.join(filename_parts)
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
            if 'edit' in request.base_url:
                if file:
                    db.execute(
                    """UPDATE recipes
                    SET username = ?, title = ?, ingredients = ?, steps = ?, image_path = ?, allergies = ?, type = ?
                    WHERE id = ?;""",
                    (g.user, form.title.data, form.ingredients.data, form.steps.data, image_path_db, form.allergies.data, form.type.data, recipe['id'])
                )
                else:
                    db.execute(
                        """UPDATE recipes
                        SET username = ?, title = ?, ingredients = ?, steps = ?, allergies = ?, type = ?
                        WHERE id = ?;""",
                        (g.user, form.title.data, form.ingredients.data, form.steps.data, form.allergies.data, form.type.data, recipe['id'])
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
    if form.file.data:
        if process_recipe_form(None):
            return redirect('home')
    notGuest = bool(g.user) #if g.user exists 
    return render_template('recipe_upload.html', form=form, notGuest = notGuest)


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
    notGuest = bool(g.user) #if g.user exists 
    return render_template('recipe_upload.html', form=form, notGuest = notGuest)

@app.route('/delete/<int:id>', methods=['GET', 'POST'])
@login_required
def delete(id):
    db = get_db()
    db.execute("""DELETE FROM recipes WHERE id = ?;""",(id,))
    db.commit()
    flash('You successfully deleted this recipe.')
    return redirect(url_for('home'))

@app.route('/delete_review/<int:review_id>', methods=['GET', 'POST'])
@login_required
def delete_review(review_id):
    db = get_db()
    recipe = db.execute("""SELECT recipe_id FROM reviews WHERE id = ?;""", (review_id,)).fetchone()
    db.execute("""DELETE FROM reviews WHERE id = ?;""",(review_id,))
    db.commit()
    flash('You successfully deleted this review.')
    return redirect(url_for('open_recipe', id = recipe['recipe_id']))

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

# here we load the recipes for home and favourites
def loading_recipes(form, recipes, filters,  page, total_pages, route):
        if g.user:
            return render_template('index.html', recipes = recipes, notGuest = True, form=form, message = filters, page = page, total_pages = total_pages, route = route)    
        else:
            return render_template('index.html', recipes = recipes, notGuest = False, form=form, message = filters, page = page, total_pages = total_pages, route = route)

@app.route('/open_favourites/<username>', methods=['GET', 'POST'])
@login_required
def open_favourites(username):
    PER_PAGE = 9
    form = Filters()
    db = get_db()

    page = request.args.get('page', 1, type=int)
    start = (page - 1) * PER_PAGE
    end = start + PER_PAGE

    prompt = form.search.data
    filters = form.type_checkboxes.data
    recipes = db.execute(
            """SELECT * FROM recipes
            WHERE id in (
                SELECT recipe_id FROM favourites
                WHERE username = ?
            );""", (g.user,)).fetchall()
    total_recipes = len(recipes)
    if prompt and filters:
         # we need the intersection of both after filtering the passed recipes
        searched_for = search_for(prompt, recipes)
        filtered = checkFilters(recipes, filters)
        recipes = list(set(searched_for) & set(filtered))
        total_recipes = len(recipes)
    elif prompt:
        recipes = search_for(prompt, recipes)
        total_recipes = len(recipes)
    elif filters:
        recipes = checkFilters(recipes, filters)
        total_recipes = len(recipes)
        
    total_pages = (total_recipes + PER_PAGE - 1) // PER_PAGE
    recipes = recipes[start:end]
    return loading_recipes(form, recipes, filters, page, total_pages, route = 'open_favourites')


@app.route('/open_my_recipes/<username>', methods=['GET', 'POST'])
@login_required
def open_my_recipes(username):
    PER_PAGE = 9
    form = Filters()
    db = get_db()

    page = request.args.get('page', 1, type=int)
    start = (page - 1) * PER_PAGE
    end = start + PER_PAGE

    prompt = form.search.data
    filters = form.type_checkboxes.data
    recipes = db.execute(
        """SELECT * FROM recipes
        WHERE username = ? ;""", (g.user,)).fetchall()
    total_recipes = len(recipes)
    if prompt and filters:
         # we need the intersection of both after filtering the passed recipes
        searched_for = search_for(prompt, recipes)
        filtered = checkFilters(recipes, filters)
        recipes = list(set(searched_for) & set(filtered))
        total_recipes = len(recipes)
    elif prompt:
        recipes = search_for(prompt, recipes)
        total_recipes = len(recipes)
    elif filters:
        recipes = checkFilters(recipes, filters)
        total_recipes = len(recipes)

    total_pages = (total_recipes + PER_PAGE - 1) // PER_PAGE
    recipes = recipes[start:end]
    return loading_recipes(form, recipes, filters, page, total_pages, route = 'open_my_recipes')
    

#here we check the filters and execute searches based on them
def checkFilters(recipes, filters):
    # Filtering recipes based on the passed filters
    filtered_recipes = [recipe for recipe in recipes if recipe['type'] in filters]
    return filtered_recipes


@app.route('/', methods=['GET', 'POST'])
@app.route('/home', methods=['GET', 'POST'])
def home():
    PER_PAGE = 9
    form = Filters()
    db = get_db()
    filters = form.type_checkboxes.data
    prompt = form.search.data

    recipes = db.execute("""SELECT * FROM recipes;""").fetchall()

    # Get the current page number from the URL query parameter
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * PER_PAGE
    end = start + PER_PAGE

    if prompt and filters:
        searched_for = search_for(prompt, recipes)
        filtered = checkFilters(searched_for, filters)
        recipes = list(set(searched_for) & set(filtered))
        total_recipes = len(recipes)
    elif prompt:
        recipes = search_for(prompt, recipes) 
        recipes = search_for(prompt=prompt, recipes=recipes)
        total_recipes = len(recipes)
    elif filters:
        filtered = checkFilters(recipes, filters)
        recipes = checkFilters(recipes, filters)
        total_recipes = len(recipes)
    else:
        total_recipes = len(recipes)

    # Calculate total pages for pagination
    total_pages = (total_recipes + PER_PAGE - 1) // PER_PAGE

    recipes = recipes[start:end]  # Slice recipes for current page

    return loading_recipes(form, recipes, filters, page, total_pages, route = 'home')


def search_for(prompt, recipes):
    db = get_db()
    form = Filters()
    searched_for = [recipe for recipe in recipes if prompt.lower() in recipe['title'].lower()]
    return searched_for

@app.route('/open_recipe/<int:id>', methods=['GET', 'POST'])
def open_recipe(id):
    form = UploadForm()
    review_form = ReviewForm()
    db = get_db()
    reviews = db.execute("""SELECT * FROM reviews
                WHERE recipe_id = ?;""", (id,)).fetchall()
    # Submitting review
    if review_form.validate_on_submit():
        db.execute(
            """INSERT INTO reviews (recipe_id, username, feedback, score)
            VALUES (?, ?, ?, ?);""",
            (id, g.user, review_form.feedback.data, review_form.score.data)
        )
        db.commit()
        # Reset the review_form fields after successful submission
        review_form.score.data = 0
        review_form.feedback.data = ''
        # Redirect to the same recipe page after submitting the review
        return redirect(url_for('open_recipe', id=id))
    else:
        review_form.score.data = 0
        review_form.feedback.data = ''
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
        
        if g.user:
            if favourite:
                for users in favourite:
                    if g.user in users['username']:
                        filename = 'star_full.png'
                    else:
                        filename = 'star_empty.png'
            else:
                filename = 'star_empty.png'
        else:
            filename = 'star_empty.png'
        notGuest = True if g.user else False # essentially checks if you are logged in or not
        avg_score = db.execute("""SELECT AVG(score) AS score
                                FROM reviews
                                WHERE recipe_id = ?;""", (id,)).fetchone()
        if publisher and publisher['username'] is not None:
            if publisher['username'] == g.user or g.user == 'admin':
                has_reviewed = True
                recipe = db.execute("SELECT * FROM recipes WHERE id = ?;", (id,)).fetchone()
                steps_string = recipe['steps']
                numbered_steps = re.findall(r'\d+\.\s*.*?(?=\d+\.\s*|\Z)', steps_string, re.DOTALL) # a regular expression to split the step while keeping the number
                return render_template('open_recipe.html', recipe=recipe, publisher=True, form=form, notGuest=notGuest, filename=filename, review_form = review_form, reviews = reviews, has_reviewed = has_reviewed, user = g.user, avg_score = avg_score['score'], steps = numbered_steps)
            else:
                 # Check if the current user has not left a review for this recipe
                has_reviewed = any(review['username'] == g.user for review in reviews)
                recipe = db.execute("SELECT * FROM recipes WHERE id = ?;", (id,)).fetchone()
                steps_string = recipe['steps']
                numbered_steps = re.findall(r'\d+\.\s*.*?(?=\d+\.\s*|\Z)', steps_string, re.DOTALL) # a regular expression to split the step while keeping the number
                return render_template('open_recipe.html', recipe=recipe, publisher=False, form=form, notGuest=notGuest,filename = filename, review_form = review_form, reviews = reviews, has_reviewed = has_reviewed, user = g.user, avg_score = avg_score['score'], steps = numbered_steps)
        else:
            return "Recipe not found", 404

@app.route('/open_random_recipe', methods=['GET'])
def open_random_recipe():
    db = get_db()
    recipes = db.execute("""SELECT id FROM recipes;""").fetchall()
    random_recipe = choice(recipes) 
    print(random_recipe)
    return redirect(url_for('open_recipe', id = random_recipe['id']))

# 404 not found error
@app.errorhandler(404)
def not_found(e): 
  return render_template("404.html") 