
import os
import logging
import requests
from sqlalchemy.exc import IntegrityError
from models import connect_db, User, SearchTerm, db
from flask_uploads import UploadSet, configure_uploads, IMAGES
from forms import SearchForm, AddUserForm, EditUserForm, LoginForm, EditProfilePicForm
from flask import Flask, Blueprint, render_template, flash, redirect, request, session, g
from flask import send_from_directory, url_for

app = Flask(__name__, static_folder='static')

# Add configurations
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL', 'postgresql:///bookwis')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config["UPLOADED_PHOTOS_DEST"] = "static/uploads"
app.config["SECRET_KEY"] = os.urandom(24)

photos = UploadSet("photos", IMAGES)
configure_uploads(app, photos)

# Create a logger and set the logging level
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

# Connect to database and create tables
connect_db(app)

###################### - Creating a default user / guest user profile ####################
DEFAULT_USER_ID = 1


def setup_default_user():
    # Provide the necessary details for the default user
    default_user = User.signup(
        username="guest",
        email="guest@bookwis.com",
        password="guestwis",
        first_name="Guest",
        last_name="User",
        profile_pic=User.profile_pic.default.arg,
        is_default=True)
    return default_user


# Use app context to create tables
with app.app_context():
    db.create_all()
    # Check if default user exists if not create the default user.
    if not db.session.query(User).filter_by(is_default=True).first():
        default_user = setup_default_user()
        db.session.add(default_user)
        db.session.commit()

# User signup/login/logout

CURR_USER_KEY = "curr_user"


@app.before_request
def add_user_to_g():
    """
    # Set a default value for g.user
    If logged in, add curr user to Flask global."""

    user_id = session.get(CURR_USER_KEY)
    if user_id:
        g.user = db.session.get(User, user_id)
    else:
        g.user = None


def do_login(user):
    """Log in user."""
    session[CURR_USER_KEY] = user.id


def do_logout():
    # Get the user id from the session
    user_id = session.get(CURR_USER_KEY)

    # If no user is logged in, flash a message and redirect to login page
    if user_id is None:
        flash("No user is currently logged in.")
        return redirect(url_for('login'))

    # Retrieve the user from the database
    user = User.query.get(user_id)
    if user:
        print(f"{user.username} logged out")

    # Clear the current user key from the session
    session.pop(CURR_USER_KEY, None)
    print(f"{session.get(CURR_USER_KEY)} - in session")
    # Clear the user object from the global context
    g.user = None
    print(f"{g.user} - in global.")

    flash("Logged out successfully!")
    return redirect(url_for('login'))
# Route to serve uploaded files


@app.route("/uploads/<filename>")
def get_file(filename):
    return send_from_directory(app.config["UPLOADED_PHOTOS_DEST"], filename)

# Signup route


@app.route('/signup', methods=["GET", "POST"])
def signup():
    """Handle user signup. Create new user and add to DB. Redirect to home page."""
    form = AddUserForm()
    if form.validate_on_submit():
        try:
            if form.profile_pic.data:
                filename = photos.save(form.profile_pic.data)
                file_url = url_for('get_file', filename=filename)

            user = User.signup(
                username=form.username.data,
                password=form.password.data,
                email=form.email.data,
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                profile_pic=file_url or User.profile_pic.default.arg,
                is_default=False
            )

            db.session.commit()
        except IntegrityError as e:
            db.session.rollback()
            flash("Great username, but it's already taken", 'danger')
            return render_template('signup.html', form=form)

        do_login(user)
        return redirect("/")
    else:
        return render_template('signup.html', form=form)

# Login route


@app.route('/login', methods=["GET", "POST"])
def login():
    """Handle user login."""
    form = LoginForm()
    if form.validate_on_submit():
        user = User.authenticate(form.username.data, form.password.data)
        if user:
            do_login(user)
            return redirect("/")
        flash("Invalid credentials.", 'danger')
    return render_template('login.html', form=form)

# Logout route


@app.route('/logout')
def logout():
    """Handle logout of user."""
    do_logout()
    flash("You are successfully logged out.", "success")
    return redirect("/login")

# Search method helpers


def handle_empty_search_term(search_term):
    if not search_term:
        logger.warning("Search term is empty.")
        return True
    return False


def get_google_books_api_key():
    api_key = os.environ.get('GOOGLE_BOOKS_API_KEY', '')
    if not api_key:
        flash("Error: Google Books API key is not set.", 'danger')
    return api_key

# Routes for searching and querying the Google API


def search_books(search_term):
    base_url = "https://www.googleapis.com/books/v1/volumes"
    api_key = get_google_books_api_key()
    if not api_key or handle_empty_search_term(search_term):
        return None

    params = {
        'q': search_term,
        'key': api_key,
        'maxResults': 24
    }

    try:
        response = requests.get(base_url, params=params)
        if response.status_code == 200:
            return response.json().get('items', [])
        else:
            logger.error(f"Error: {response.status_code}")
            return None
    except Exception as e:
        logger.exception(
            "An error occurred while making the API request. Error: %s", str(e))
        return None


def get_book(volume_id):
    base_url = f"https://www.googleapis.com/books/v1/volumes/{volume_id}"
    api_key = get_google_books_api_key()
    if not api_key:
        return None

    params = {'key': api_key}

    try:
        response = requests.get(base_url, params=params)

        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Error: {response.status_code}")
            return None
    except Exception as e:
        logger.exception(
            "An error occurred while making the API request. Error: %s", str(e))
        return None

# Routes for different resources
# Grouping routes for similar resources together


@app.route("/")
def homepage():
    """ Show the home page with a default search """
    form = SearchForm()
    search_term = "beach romance"
    result = search_books(search_term)
    return render_template("index.html", form=form, search_term=search_term, results=result)


@app.route("/search", methods=['POST'])
def search():
    """ Handle search originating from the home page """
    form = SearchForm()
    search_term = form.search_term.data

    if not search_term:
        flash("Please enter a search term.", "danger")
        return redirect("/")

    if g.user:
        user_id = g.user.id
    else:
        user_id = DEFAULT_USER_ID

    phrase = SearchTerm(term=search_term, user_id=user_id)
    db.session.add(phrase)
    db.session.commit()

    return redirect("/results?search_term={}".format(search_term))


@app.route("/results", methods=['GET', 'POST'])
def show_results():
    """ Search the API and show results """
    form = SearchForm()
    search_term = request.args.get('search_term', '')
    result = search_books(search_term)

    if result:
        items = result
        return render_template("results.html", form=form, search_term=search_term, results=items)
    else:
        flash("Failed to fetch data from the Google Books API.", "danger")
        return redirect("/")


@app.route("/profile")
def show_profile():
    """ Show user profile """
    if not g.user:
        flash("Access unauthorized - Please login!", "danger")
        return redirect("/login")

    searches = (SearchTerm
                .query
                .filter(SearchTerm.user_id == g.user.id)
                .order_by(SearchTerm.timestamp.desc())
                .limit(100)
                .all())

    return render_template("profile.html", search_history=searches)

# Edit and update profile routes


@app.route('/profile/edit', methods=["GET", "POST"])
def edit_profile():
    """Update profile for the current user."""
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/login")

    if g.user.is_default:
        flash('Cannot edit default user', "warning")
        return redirect("/profile")

    form = EditUserForm(obj=g.user)
    if form.validate_on_submit():
        try:
            user = User.authenticate(
                username=form.username.data,
                password=form.password.data
            )

            if user:
                User.update_user_data(user, form)
                db.session.commit()
                flash("Profile updated successfully!", "success")
                return redirect("/profile")
            else:
                flash("Invalid password - profile not updated.", 'danger')
                return redirect("/")

        except IntegrityError:
            flash("Error updating profile, invalid credentials.")

    return render_template("edit.html", form=form)


@app.route("/profile/photo", methods=['GET', 'POST'])
def update_profile_photo():
    """ Update profile picture. """
    if not g.user:
        flash("Access unauthorized - Please login!", "danger")
        return redirect("/login")

    form = EditProfilePicForm()
    if form.validate_on_submit():
        try:
            filename = photos.save(form.profile_pic.data)
            file_url = url_for('get_file', filename=filename)
            g.user.profile_pic = file_url
            db.session.commit()

            flash("Profile pic updated successfully!", "success")
            return redirect("/profile")

        except IntegrityError:
            flash("Error updating profile, invalid password.")

    return render_template("photo.html", form=form)

# Delete user route


@app.route('/profile/delete', methods=["POST"])
def delete_user():
    """Delete user."""
    if g.user is None:
        flash("Access unauthorized.", "danger")
        return redirect("/login")

    if g.user.is_default:
        flash("You are not authorized to delete this user.", "danger")
        return redirect("/profile")

    user_to_delete_id = request.args.get('user_id')
    if g.user.id != int(user_to_delete_id):

        flash("You can only delete your own account!")
        return redirect(url_for('profile'))

    do_logout()

    db.session.delete(g.user)
    db.session.commit()
    flash("Sad to see you go, account deleted successfully!", "success")
    return redirect("/signup")

# Author and book details routes


@app.route("/author/<name>", methods=['GET'])
def show_author(name):
    """ Show author details and released books """
    form = SearchForm()
    search_term = name
    result = search_books(search_term)
    return render_template("author.html", form=form, search_term=search_term, results=result)


@app.route("/books/<volume_id>", methods=['GET'])
def show_book(volume_id):
    """ Retrieve and show information on a specific book"""
    result = get_book(volume_id)
    return render_template('book.html', item=result)
