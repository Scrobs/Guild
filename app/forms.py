# app/forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo

class LoginForm(FlaskForm):
    username = StringField('Name', validators=[DataRequired(), Length(min=1, max=150)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=1, max=128)])
    submit = SubmitField('Login')

class PasswordResetForm(FlaskForm):
    password = PasswordField('New Password', validators=[DataRequired(), Length(min=6, max=128)])
    confirm = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')

class VoteForm(FlaskForm):
    submit = SubmitField('Vote')
