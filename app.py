from flask import Flask, render_template, request, redirect, session, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date
import os
import json

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "supersecretkey")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# MODELLI
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(512), nullable=False)
    teams = db.relationship("Team", backref="owner", lazy=True)

class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    giocatori = db.Column(db.Text, nullable=False)
    data = db.Column(db.Date, default=date.today, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

# UTILS
def oggi():
    return date.today()

# ROTTE UTENTE
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        if User.query.filter((User.email == email) | (User.username == username)).first():
            return "Utente già esistente", 400

        hashed_pw = generate_password_hash(password)
        nuovo = User(username=username, email=email, password_hash=hashed_pw)
        db.session.add(nuovo)
        db.session.commit()
        return redirect("/login")

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    errore = None
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            session["user_id"] = user.id
            return redirect("/")
        errore = "Credenziali errate. Riprova."

    return render_template("login.html", errore=errore)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# HOME E GESTIONE PRENOTAZIONI
@app.route("/", methods=["GET", "POST"])
def index():
    if "user_id" not in session:
        return redirect("/login")

    teams = Team.query.filter_by(user_id=session["user_id"], data=oggi()).all()

    if request.method == "POST":
        nomi = request.form["nomi"].split(",")
        squadra = [nome.strip() for nome in nomi if nome.strip()]
        if squadra:
            nuova = Team(giocatori=json.dumps(squadra), data=oggi(), user_id=session["user_id"])
            db.session.add(nuova)
            db.session.commit()
        return redirect("/")

    return render_template("index.html", prenotazioni=[json.loads(t.giocatori) for t in teams])

@app.route("/rimuovi", methods=["POST"])
def rimuovi():
    if "user_id" not in session:
        return "", 401
    index = request.json.get("index")
    teams = Team.query.filter_by(user_id=session["user_id"], data=oggi()).all()
    if 0 <= index < len(teams):
        db.session.delete(teams[index])
        db.session.commit()
    return "", 204

@app.route("/duplica", methods=["POST"])
def duplica():
    if "user_id" not in session:
        return "", 401
    index = request.json.get("index")
    teams = Team.query.filter_by(user_id=session["user_id"], data=oggi()).all()
    if 0 <= index < len(teams):
        squadra = json.loads(teams[index].giocatori)
        nuova = Team(giocatori=json.dumps(squadra), data=oggi(), user_id=session["user_id"])
        db.session.add(nuova)
        db.session.commit()
    return "", 204

@app.route("/dati")
def dati():
    if "user_id" not in session:
        return jsonify([])
    teams = Team.query.filter_by(user_id=session["user_id"], data=oggi()).all()
    return jsonify({
        "data": oggi().isoformat(),
        "prenotazioni": [json.loads(t.giocatori) for t in teams]
    })

@app.route("/aggiungi", methods=["POST"])
def aggiungi():
    if "user_id" not in session:
        return "", 401
    squadra = request.json.get("squadra", [])
    if 3 <= len(squadra) <= 5:
        nuova = Team(giocatori=json.dumps(squadra), data=oggi(), user_id=session["user_id"])
        db.session.add(nuova)
        db.session.commit()
    return "", 204

# START
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, host="0.0.0.0", port=3000)
