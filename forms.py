import email_validator
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms.validators import DataRequired, Email, Length


class SearchForm(FlaskForm):
    """Search form."""
    search_term = StringField(
        'Search for a Book, Author or Interest.', validators=[DataRequired()])


class AddUserForm(FlaskForm):
    """Form for adding users."""

    username = StringField('Username', validators=[DataRequired()])
    email = StringField('E-mail', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[Length(min=6)])
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    profile_pic = FileField('(Optional) Upload Image', validators=[
                            FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')])


class LoginForm(FlaskForm):
    """Login form."""

    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[Length(min=6)])


class EditUserForm(FlaskForm):
    """ Form for editing a user """

    username = StringField('Username', validators=[
                           DataRequired(), Length(min=3, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])

    first_name = StringField(
        'First Name', validators=[Length(max=255)])
    last_name = StringField('Last Name', validators=[Length(max=255)])
    password = PasswordField(
        'Enter your password to confirm', validators=[Length(min=6)])


class EditProfilePicForm(FlaskForm):
    """ Form for updating profile image """
    profile_pic = FileField('Upload profile Image', validators=[
                            FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!'), FileRequired("Please select a photo from your files")])
