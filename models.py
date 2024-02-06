from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from datetime import datetime, timezone

db = SQLAlchemy()
bcrypt = Bcrypt()

# Connect to the database


def connect_db(app):
    db.app = app
    db.init_app(app)


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, autoincrement=True,
                   primary_key=True, nullable=False)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.Text, nullable=False)
    email = db.Column(db.String(50), nullable=False, unique=True)
    first_name = db.Column(db.String(30), nullable=False)
    last_name = db.Column(db.String(30), nullable=False)
    profile_pic = db.Column(
        db.String(255), default="/static/default.jpeg", nullable=True)
    search_history = db.relationship('SearchTerm', backref="user")
    is_default = db.Column(db.Boolean, default=False)

    def get_id(self):
        return self.id

    @classmethod
    def signup(cls, username, email, password, first_name, last_name, profile_pic, is_default):
        """Sign up user.

        Hashes password and adds user to system.
        """
        hashed_pwd = bcrypt.generate_password_hash(password).decode('UTF-8')
        user = User(username=username, email=email,
                    password=hashed_pwd, first_name=first_name, last_name=last_name, profile_pic=profile_pic, is_default=is_default)
        db.session.add(user)
        return user

    @classmethod
    def authenticate(cls, username, password):
        """Find user with `username` and `password`.

        This is a class method (call it on the class, not an individual user.)
        It searches for a user whose password hash matches this password
        and, if it finds such a user, returns that user object.

        If can't find matching user (or if password is wrong), returns False.
        """
        user = cls.query.filter_by(username=username).first()

        if user:
            is_auth = bcrypt.check_password_hash(user.password, password)
            if is_auth:
                return user

        return False

    @classmethod
    def update_user_data(cls, user, form):
        user.username = form.username.data
        user.email = form.email.data
        user.first_name = form.first_name.data
        user.last_name = form.last_name.data


class SearchTerm(db.Model):
    __tablename__ = "search_terms"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    term = db.Column(db.String())
    timestamp = db.Column(db.DateTime, nullable=False,
                          default=datetime.now(timezone.utc))
