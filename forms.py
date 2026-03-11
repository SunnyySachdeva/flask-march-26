from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField, EmailField, PasswordField
from wtforms.validators import InputRequired, Email, NumberRange, Length, EqualTo
from flask_ckeditor import CKEditorField

class ContactForm(FlaskForm):
    name = StringField(label="Your Name", validators=[InputRequired()])
    email = EmailField(label="Your Email", validators=[InputRequired(), Email()])
    phone = IntegerField(label="Your Phone Number", validators=[InputRequired(), NumberRange(min=1111111111, max=9999999999)])
    body = CKEditorField(label="Your Message", validators=[InputRequired()])
    submit = SubmitField(label="Submit", render_kw={"class": "btn btn-dark"})

class LoginForm(FlaskForm):
    email = StringField(label="Email", validators=[InputRequired(), Email()])
    password = PasswordField(label="Password", validators=[InputRequired()])
    submit = SubmitField(label="Login", render_kw={"class": "btn btn-dark"})

class RegisterForm(FlaskForm):
    name = StringField(label="Name", validators=[InputRequired()])
    email = StringField(label="Email", validators=[InputRequired(), Email()])
    password = PasswordField(label="Password", validators=[InputRequired(), Length(min=10, max=16, message="Password must be at least 10 characters long")])
    password_confirm = PasswordField(label="Confirm Password", validators=[EqualTo(fieldname='password', message="Passwords must match")])
    submit = SubmitField(label="Login", render_kw={"class": "btn btn-dark"})

class PostForm(FlaskForm):
    title = StringField(label="Post Title", validators=[InputRequired()])
    subtitle = StringField(label="Post Subtitle", validators=[InputRequired()])
    img_url = StringField(label="URL of your post background", validators=[InputRequired()])
    body = CKEditorField(label="The Post itself", validators=[InputRequired()])
    submit = SubmitField(label="Submit", render_kw={"class": "btn btn-dark"})


class CommentForm(FlaskForm):
    commend_body = CKEditorField(label="Your Comment", validators=[InputRequired()])
    submit = SubmitField(label="Submit", render_kw={"class": "btn btn-dark"})

