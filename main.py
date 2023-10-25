import flask
import flask_bootstrap

app = flask.Flask(__name__)
app.config['SECRET_KEY'] = "8BYkEfBA6O6donzWlSihBXox7C0sKR6b"  # os.environ.get("SECRET_KEY")
flask_bootstrap.Bootstrap(app)


@app.route('/')
def home():
    return flask.render_template(
        "index.html"
    )


@app.route('/portfolio', methods=["GET", "POST"])
def portfolio():
    return flask.render_template(
        'portfolio.html'
    )


@app.route("/about")
def about():
    return flask.render_template("about.html")


@app.route("/contact")
def contact():
    return flask.render_template("contact.html")


@app.route("/thanks", methods=['GET', 'POST'])
def thanks():
    return flask.render_template("thanks.html")


if __name__ == "__main__":
    app.run(debug=True)
