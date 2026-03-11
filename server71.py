from flask import Flask, render_template, redirect, flash, url_for, abort

from sqlalchemy import String, Integer, Date, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from flask_sqlalchemy import SQLAlchemy

from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin

from flask_ckeditor import CKEditor
from flask_bootstrap import Bootstrap5

from communication import Email
from forms import ContactForm, LoginForm, RegisterForm, CommentForm, PostForm

from datetime import datetime
import os
from typing import List
from functools import wraps

app = Flask(__name__, template_folder="all_templates", static_folder="all_static_files")
app.secret_key = os.environ.get('APP_SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('SQLALCHEMY_URI')
current_year = datetime.now().year

ckeditor = CKEditor(app)
bootstrap = Bootstrap5(app)

# Database
class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
db.init_app(app)

class User(db.Model, UserMixin):
    __tablename__ = "user"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String[200], nullable=False)
    email: Mapped[str] = mapped_column(String[300], nullable=False)
    password: Mapped[str] = mapped_column(String[500], nullable=False)
    date_joined: Mapped[Date] = mapped_column(Date, default=datetime.now().date())

    posts: Mapped[List['Post']] = relationship(back_populates='author')
    comments: Mapped[List['Comment']] = relationship(back_populates='author')

    def __repr__(self):
        return f"<User {self.id}: {self.name}>"

class Post(db.Model):
    __tablename__ = 'post'
    id:Mapped[int] = mapped_column(Integer, primary_key=True)
    title:Mapped[str] = mapped_column(String[400], nullable=False)
    subtitle: Mapped[str] = mapped_column(String[500], nullable=False)
    body: Mapped[str] = mapped_column(String[2000], nullable=False)
    img_url: Mapped[str] = mapped_column(String[500], nullable=False)
    date_created: Mapped[Date] = mapped_column(Date, nullable=False, default=datetime.now().date())
    date_last_modified: Mapped[Date] = mapped_column(Date, nullable=True)

    author_id: Mapped[int] = mapped_column(ForeignKey('user.id'))
    author: Mapped['User'] = relationship(back_populates='posts')

    comments: Mapped[List['Comment']] = relationship(back_populates='post')

    def __repr__(self):
        return f"<Post {self.id}: {self.title}>"

class Comment(db.Model):
    __tablename__ = "comment"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    comment: Mapped[str] = mapped_column(String[1000], nullable=False)

    # parent user
    author_id: Mapped[int] = mapped_column(ForeignKey('user.id'))
    author: Mapped['User'] = relationship(back_populates='comments')
    # parent post
    post_id: Mapped[int] = mapped_column(ForeignKey('post.id'))
    post: Mapped['Post'] = relationship(back_populates='comments')

    def __repr__(self):
        return f"<Comment {self.id} on post {self.post_id} by author {self.author_id}>"


with app.app_context():
    db.create_all()

# LOGIN TASK
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)

def post_owner(func):
    @wraps(func)
    def wrapper_func(*args, **kwargs):
        selected_post = db.session.execute(db.select(Post).where(Post.id == kwargs['post_id'])).scalar()
        if selected_post:
            if selected_post.author_id == current_user.id:
                return func(*args, **kwargs)
            else:
                return abort(403)
        else:
            return abort(404)
    return wrapper_func


##########################-----------  VIEWS   -----------##########################

@app.route("/", methods=['POST', 'GET'])
def home():
    posts = db.session.execute(db.select(Post)).scalars().all()
    if posts:
        return render_template("pages/index.html", year=current_year, posts=posts)
    else:
        return render_template("pages/index.html", year=current_year, posts=False)

@app.route("/contact", methods=['POST', 'GET'])
def contact():
    form = ContactForm()
    if form.validate_on_submit():
        email = Email()
        user_email = form.email.data
        message = f"Name: {form.name.data}\nemail: {user_email}\nPhone: {form.phone.data}\nMessage: {form.body.data}"
        if email.send(message=message, user_email=user_email):
            return render_template("pages/contact.html", year=current_year, form=form, message_sent=0)
        else:
            return render_template("pages/contact.html", year=current_year, form=form, message_sent=1)
    return render_template("pages/contact.html", year=current_year, form=form, message_sent=2)

@app.route('/about')
def about():
    return render_template("pages/about.html", year=current_year)

@app.route('/login', methods=['POST', 'GET'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user_exists = db.session.execute(db.select(User).where(User.email == form.email.data)).scalar()
        if user_exists:
            if check_password_hash(user_exists.password, form.password.data):
                login_user(user_exists)
                return redirect(url_for('home'))
            else:
                flash("Wrong Credentials")
                return redirect(url_for('login'))
        else:
            flash("User doesn't exist. Please register first.")
            return redirect(url_for('register'))
        return redirect(url_for('home'))
    return render_template('pages/login.html', form=form, year=current_year)

@app.route('/register', methods=['POST', 'GET'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        email_exists = db.session.execute(db.select(User).where(User.email == form.email.data)).scalar()
        if email_exists:
            flash("Email already registered with us. Please login instead.")
            return redirect(url_for('login'))
        else:
            new_user = User(
                name=form.name.data,
                email=form.email.data,
                password=generate_password_hash(form.password.data, method='scrypt', salt_length=16),
            )
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for('home'))
    return render_template('pages/register.html', form=form, year=current_year)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/create', methods=['POST', 'GET'])
@login_required
def create():
    form = PostForm()
    if form.validate_on_submit():
        new_post = Post(
            title = form.title.data,
            subtitle = form.subtitle.data,
            body = form.body.data,
            author_id = current_user.id,
            img_url = form.img_url.data
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('pages/make.html', form=form, year=current_year)

@app.route('/post/<int:post_id>', methods=['POST', 'GET'])
def post(post_id):
    selected_post = db.session.execute(db.select(Post).where(Post.id == post_id)).scalar()
    form = CommentForm()
    if form.validate_on_submit():
        if current_user.is_authenticated:
            new_comment = Comment(
                comment = form.commend_body.data,
                author_id = current_user.id,
                post_id = selected_post.id
            )
            db.session.add(new_comment)
            db.session.commit()
            return redirect(url_for('post', post_id=selected_post.id))
        else:
            flash("You need to login first to post comments")
            return redirect(url_for('login'))
    if selected_post:
        return render_template("pages/post.html", post=selected_post, year=current_year, form=form)
    else:
        return redirect(url_for('home'))

@app.route("/edit/<int:post_id>", methods=['POST', 'GET'])
@login_required
@post_owner
def edit(post_id):
    form = PostForm()
    selected_post = db.session.execute(db.select(Post).where(Post.id == post_id)).scalar()
    if form.validate_on_submit():
        selected_post.title = form.title.data
        selected_post.body = form.body.data
        selected_post.subtitle = form.subtitle.data
        selected_post.img_url = form.img_url.data
        selected_post.date_last_modified = datetime.now().date()
        db.session.commit()
        return redirect(url_for('post', post_id=post_id))
    else:
        if selected_post:
            form.title = selected_post.title
            form.subtitle = selected_post.subtitle
            form.body = selected_post.body
            form.img_url = selected_post.img_url
            return render_template("pages/make.html", form=form, year=current_year)
        else:
            return redirect(url_for("home"))


@app.route('/delete/<int:post_id>')
@login_required
@post_owner
def delete(post_id):
    post = db.session.execute(db.select(Post).where(Post.id == post_id)).scalar()
    if post:
        comments = post.comments
        for comment in comments:
            db.session.delete(comment)
        db.session.delete(post)
        db.session.commit()
        return redirect(url_for('home'))
    else:
        return redirect(url_for('home'))


if __name__ == "__main__":
    app.run(debug=True, port=5071, host="0.0.0.0")
