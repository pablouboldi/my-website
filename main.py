from flask import Flask, render_template, redirect, url_for, flash, abort
from flask_bootstrap import Bootstrap

app = Flask(__name__)
app.config['SECRET_KEY'] = "8BYkEfBA6O6donzWlSihBXox7C0sKR6b"  # os.environ.get("SECRET_KEY")
Bootstrap(app)


@app.route('/')
def home():
    return render_template(
        "index.html"
    )


@app.route('/portfolio', methods=["GET", "POST"])
def portfolio():
    return render_template(
        'portfolio.html'
    )


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route("/thanks", methods=['GET', 'POST'])
def thanks():
    return render_template("thanks.html")


if __name__ == "__main__":
    app.run(debug=True)

# TODO 1: Arreglar la navbar transparente porque en celular se mete sobre la imagen principal de la pagina
# TODO 2: Revisar el esquema de colores
# TODO 3: Ver si conviene agregar mas cosas en las distintas paginas porque se ve muy corta en un celular
# TODO 4: Agregar informacion en la pagina "about"
