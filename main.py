from functools import wraps
from flask import Flask, render_template, redirect, url_for, flash, abort
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from datetime import date
import os

from sqlalchemy.ext.declarative import declarative_base
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from forms import CreatePostForm, LoginForm, RegisterForm, CommentForm
from flask_gravatar import Gravatar

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")
ckeditor = CKEditor(app)
Bootstrap(app)

# # CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL1",  "sqlite:///blog.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Creo un objeto de clase LoginManager
login_manager = LoginManager()
# Le digo al objeto login_manager que trabaje con el objeto app
login_manager.init_app(app)
# Defino la función a la que se dirige por default si el login del usuario es inválido.
login_manager.login_view = "login"

Base = declarative_base()


# # CONFIGURE TABLES
class User(Base, UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(250), unique=True, nullable=False)
    password = db.Column(db.String(250), nullable=False)
    name = db.Column(db.String(250), nullable=False)

    # La clase User tiene 2 hijos, entonces tiene 2 relaciones con los hijos a definir

    # *************** Child Relationship ************* #
    posts = relationship("BlogPost", back_populates="author")

    # *************** Child Relationship ************* #
    comments = relationship("Comment", back_populates="comment_author")


class BlogPost(Base, db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)

    # Esto es para definir a BlogPost como una clase hija de User en donde pueda haber una relación cruzada
    # entre los parámetros author, author_id y posts

    # La clase BlogPost tiene 2 padres, entonces tiene 2 relaciones con los padres a definir

    # *************** Parent Relationship ************* #
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    author = relationship("User", back_populates="posts")

    # *************** Parent Relationship ************* #
    comments = relationship("Comment", back_populates="parent_post")


class Comment(Base, db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)

    # La clase Comment tiene un padre (User) y un hijo (BLogPost)

    # *************** Parent Relationship ************* #
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    comment_author = relationship("User", back_populates="comments")

    # *************** Child Relationship ************* #
    post_id = db.Column(db.Integer, db.ForeignKey("blog_posts.id"))
    parent_post = relationship("BlogPost", back_populates="comments")


# db.create_all()


# Esto es un decorador para que solo el admin pueda agregar posts, editarlos o borrarlos
def admin_only(f):
    @wraps(f)
    def wrapper_function(*args, **kwargs):
        if current_user.is_authenticated and current_user.id != 1:
            return abort(403, description="User is not admin")
        return f(*args, **kwargs)

    return wrapper_function


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


@app.route('/')
def get_all_posts():
    posts = BlogPost.query.all()
    print(current_user)  # Esto es un atributo de flask_login
    try:
        logged_user_id = current_user.id
    except AttributeError:
        logged_user_id = None
    return render_template(
        "index.html",
        all_posts=posts,
        logged_in=current_user.is_authenticated,
        logged_user_id=logged_user_id
    )


@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        new_user_email = form.email.data

        # if new_user_email ==

        new_user_password = generate_password_hash(password=form.password.data, method='pbkdf2:sha256', salt_length=8)
        new_user_name = form.name.data

        try:
            new_user = User(email=new_user_email, password=new_user_password, name=new_user_name)
            db.session.add(new_user)
            db.session.commit()
        except:  # Deberia tratar de agarrar el error especifico. Es un IntegrityError
            flash("That email already exists. Try to login instead")
            return redirect(url_for('login'))

        login_user(new_user)  # Valido el usuario

        return redirect(url_for('get_all_posts'))
    else:
        return render_template("register.html", form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()

    if form.validate_on_submit():

        # Recupero el email ingresado en el form de la ruta login
        email = form.email.data

        # Busco el usuario correspondiente a ese email en la base de datos
        user = User.query.filter_by(email=email).first()

        # Chequeo si ese usuario existe
        if user:
            # Recupero la contraseña ingresada en el form de la ruta login
            password_entered = form.password.data

            # Chequeo la contraseña ingresada con la existente en la base de datos
            if check_password_hash(user.password, password_entered):
                login_user(user)  # Valido el usuario
                flash("Login successful!!")
                return redirect(url_for('get_all_posts'))

            # Si la contraseña es inválida, le doy feedback y lo redirijo a la función login
            else:
                flash("Wrong password - Try again!")
                return redirect(url_for('login'))

        # Si el usuario no existe, le doy feedback y lo redirijo a la función login
        else:
            flash("That user does not exist - Try again!")
            return redirect(url_for('login'))
    else:
        return render_template("login.html", form=form, logged_in=current_user.is_authenticated)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route("/post/<int:post_id>", methods=["GET", "POST"])
def show_post(post_id):
    form = CommentForm()
    requested_post = BlogPost.query.get(post_id)

    if form.validate_on_submit():
        if current_user.is_authenticated:
            new_comment = Comment(
                text=form.comment_text.data,
                comment_author=current_user,
                parent_post=requested_post
            )

            db.session.add(new_comment)
            db.session.commit()
            return redirect(url_for('show_post', post_id=post_id))
        else:
            flash("You are not logged in")
            return redirect(url_for('login'))

    user = current_user  # Esto es un atributo de flask_login
    try:
        logged_user_id = user.id
    except AttributeError:
        logged_user_id = None

    return render_template(
        "post.html",
        post=requested_post,
        logged_user_id=logged_user_id,
        logged_in=current_user.is_authenticated,
        form=form
    )


@app.route("/about")
def about():
    return render_template("about.html", logged_in=current_user.is_authenticated)


@app.route("/contact")
def contact():
    return render_template("contact.html", logged_in=current_user.is_authenticated)


@app.route("/new-post", methods=["GET", "POST"])
@admin_only
@login_required
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author=current_user.name,
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form)


@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
@admin_only
@login_required
def edit_post(post_id):
    post = BlogPost.query.get(post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.author,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.author = edit_form.author.data
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))

    return render_template("make-post.html", form=edit_form, is_edit=True, logged_in=current_user.is_authenticated)


@app.route("/delete/<int:post_id>")
@admin_only
def delete_post(post_id):
    post_to_delete = BlogPost.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


if __name__ == "__main__":
    app.run(debug=True)
