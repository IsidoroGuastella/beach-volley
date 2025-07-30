from flask import Flask, request, redirect, render_template, jsonify
import json
import os
from datetime import datetime

app = Flask(__name__)
FILE = "prenotazioni.json"

def oggi():
    return datetime.now().strftime("%Y-%m-%d")

def carica_dati():
    if not os.path.exists(FILE) or os.path.getsize(FILE) == 0:
        return {"data": oggi(), "prenotazioni": []}

    with open(FILE, "r") as f:
        try:
            dati = json.load(f)
            if dati.get("data") != oggi():
                return {"data": oggi(), "prenotazioni": []}
            return dati
        except json.JSONDecodeError:
            return {"data": oggi(), "prenotazioni": []}

def salva_dati(dati):
    dati["data"] = oggi()
    with open(FILE, "w") as f:
        json.dump(dati, f, indent=4)

@app.route("/", methods=["GET", "POST"])
def index():
    dati = carica_dati()

    if request.method == "POST":
        nomi = request.form["nomi"].split(",")
        squadra = [nome.strip() for nome in nomi if nome.strip()]
        if squadra:
            dati["prenotazioni"].append(squadra)
            salva_dati(dati)
        return redirect("/")

    return render_template("index.html", prenotazioni=dati["prenotazioni"])

@app.route("/rimuovi", methods=["POST"])
def rimuovi():
    index = request.json.get("index")
    dati = carica_dati()
    if 0 <= index < len(dati["prenotazioni"]):
        dati["prenotazioni"].pop(index)
        salva_dati(dati)
    return "", 204

@app.route("/duplica", methods=["POST"])
def duplica():
    index = request.json.get("index")
    dati = carica_dati()
    if 0 <= index < len(dati["prenotazioni"]):
        squadra = dati["prenotazioni"][index]
        dati["prenotazioni"].append(squadra.copy())
        salva_dati(dati)
    return "", 204


@app.route("/dati")
def dati():
    return jsonify(carica_dati())

@app.route("/aggiungi", methods=["POST"])
def aggiungi():
    dati = carica_dati()
    squadra = request.json.get("squadra", [])
    if 3 <= len(squadra) <= 5:
        dati["prenotazioni"].append(squadra)
        salva_dati(dati)
    return "", 204

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=3000)
