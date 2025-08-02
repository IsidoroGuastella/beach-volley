from flask import Flask, request, redirect, render_template, jsonify
import json
import os
from datetime import datetime, date
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

with app.app_context():
    db.create_all()
    print("✅ Tabelle create (Render)")

class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    giocatori = db.Column(db.Text, nullable=False)
    data = db.Column(db.Date, default=date.today)

def oggi():
    return date.today()

def carica_dati():
    teams = Team.query.filter(Team.data == oggi()).all()
    return {
        "data" : oggi(),
        "prenotazioni" : [json.loads(t.giocatori) for t in teams]
    }

@app.route("/", methods=["GET", "POST"])
def index():
    dati = carica_dati()

    if request.method == "POST":
        nomi = request.form["nomi"].split(",")
        squadra = [nome.strip() for nome in nomi if nome.strip()]
        if squadra:
            team = Team(giocatori=json.dumps(squadra), data = oggi())
            db.session.add(team)
            db.session.commit()
        return redirect("/")

    return render_template("index.html", prenotazioni=dati["prenotazioni"])

@app.route("/rimuovi", methods=["POST"])
def rimuovi():
    index = request.json.get("index")
    teams = Team.query.filter(Team.data == oggi()).all()
    if 0 <= index < len(teams):
        db.session.delete(teams[index])
        db.session.commit()
    return "", 204

@app.route("/duplica", methods=["POST"])
def duplica():
    index = request.json.get("index")
    teams = Team.query.filter(Team.data == oggi()).all()
    if 0 <= index < len(teams):
        squadra = json.loads(teams[index].giocatori)
        nuova = Team(giocatori=json.dumps(squadra), data=oggi())
        db.session.add(nuova)
        db.session.commit()
    return "", 204


@app.route("/dati")
def dati():
    return jsonify(carica_dati())

@app.route("/aggiungi", methods=["POST"])
def aggiungi():
    squadra = request.json.get("squadra",[])
    if 3 <= len(squadra) <= 5:
        nuova = Team(giocatori=json.dumps(squadra), data=oggi())
        db.session.add(nuova)
        db.session.commit()
    return "", 204

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=3000)
