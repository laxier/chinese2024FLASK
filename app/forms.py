from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
import sqlalchemy as sa
from app import db
from app.models import User
from chinese_tools import has_chinese_char


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = db.session.scalar(sa.select(User).where(User.username == username.data))
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = db.session.scalar(sa.select(User).where(User.email == email.data))
        if user is not None:
            raise ValidationError('Please use a different email address.')

    def validate_password(self, password):
        if len(password.data) < 8:
            raise ValidationError('Your password should bot be less than 8 symbols')


class DeckForm(FlaskForm):
    name = StringField('Deck name', validators=[DataRequired()])
    submit = SubmitField('Create')


class CardForm(FlaskForm):
    char = StringField('Chinese character:', validators=[DataRequired()])
    submit = SubmitField('Add')

    def validate_char(self, char):
        cleaned_text = (char.data.replace(" ", "").replace("\n", "").replace("\r", "").replace(u"\u200b", "")
                        .replace(u"\u00A0", ""))
        if has_chinese_char(cleaned_text) == False:
            raise ValidationError('Please enter a chinese character!')


class DeleteForm(FlaskForm):
    assurance = BooleanField('Ты уверен?', validators=[DataRequired()])
    submit = SubmitField('Удалить')


class AddForm(FlaskForm):
    text = TextAreaField('Введи слова с новой строки', validators=[DataRequired()])
    submit = SubmitField('Добавить')

    def validate_text(self, text):
        cleaned_text = text.data.replace(" ", "").replace("\n", "").replace("\r", "").replace(u"\u200b", "").replace(u"\u00A0", "")
        if has_chinese_char(cleaned_text) == False:
            raise ValidationError('Please enter a chinese character!')
