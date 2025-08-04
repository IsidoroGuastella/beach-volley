
# LIBRERIE NECESSARIE
from flask import Flask, render_template, request, redirect, session, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date
import smtplib
from email.mime.text import MIMEText
from token_utils import genera_token, verifica_token
import os
import json

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "supersecretkey")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# MODELLI
class User(db.Model):  # Crea la tabella user
    id = db.Column(db.Integer, primary_key=True) # Chiave primaria id
    username = db.Column(db.String(80), unique=True, nullable=False) 
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(512), nullable=False) # Viene salvata la password hashata
    is_verified = db.Column(db.Boolean, default=False) # Un flag pe verificare che l'utente sia verificato o meno
    teams = db.relationship("Team", backref="owner", lazy=True) # La chiave esterna
class Team(db.Model): # Crea la tabella team
    id = db.Column(db.Integer, primary_key=True) # Chiave primaria id
    giocatori = db.Column(db.Text, nullable=False) # Lista dei giocatori della squadra
    data = db.Column(db.Date, default=date.today, nullable=False) 
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False) # Chiave esterna associata 

# UTILS
def oggi():
    return date.today()

# ROTTE UTENTE
@app.route("/register", methods=["GET", "POST"]) # Rotta per effettuare il SIGNUP
def register(): 
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        if User.query.filter(User.email == email).first():
            return "Utente già esistente", 400

        hashed_pw = generate_password_hash(password)
        nuovo = User(username=username, email=email, password_hash=hashed_pw)
        db.session.add(nuovo)
        db.session.commit()

        # Genera il token
        token = genera_token(email)
        link = url_for("verifica_email", token=token, _external=True)

        # Invia email
        invia_email_verifica(email, link)

        return "Registrazione riuscita. Controlla la tua email per confermare l’account."

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"]) # Rotta per effettuare il LOGIN
def login():
    errore = None
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            if not user.is_verified:
                errore = "Devi verificare l'email prima di accedere."
            else:
                session["user_id"] = user.id
                return redirect("/")

        errore = "Credenziali errate. Riprova."

    return render_template("login.html", errore=errore)

@app.route("/logout") # Rotta per il LOGOUT
def logout():
    session.clear()
    return redirect("/login")

# HOME E GESTIONE PRENOTAZIONI
@app.route("/", methods=["GET", "POST"]) # Rotta per la schermata personale con le prenotazioni delle partite
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

@app.route("/rimuovi", methods=["POST"]) # Rotta per rimuovere una sqaudra inserita
def rimuovi():
    if "user_id" not in session:
        return "", 401
    index = request.json.get("index")
    teams = Team.query.filter_by(user_id=session["user_id"], data=oggi()).all()
    if 0 <= index < len(teams):
        db.session.delete(teams[index])
        db.session.commit()
    return "", 204

@app.route("/duplica", methods=["POST"]) # Rotta per diplicare in fondo alla lista una sqaudra inserita
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

@app.route("/dati") # Rotta per la visualizzazione delle partite registrate dal dato user
def dati():
    if "user_id" not in session:
        return jsonify([])
    teams = Team.query.filter_by(user_id=session["user_id"], data=oggi()).all()
    return jsonify({
        "data": oggi().isoformat(),
        "prenotazioni": [json.loads(t.giocatori) for t in teams]
    })

@app.route("/aggiungi", methods=["POST"]) # Rotta per aggiungere una squadra
def aggiungi():
    if "user_id" not in session:
        return "", 401
    squadra = request.json.get("squadra", [])
    if 2 <= len(squadra) <= 5:
        nuova = Team(giocatori=json.dumps(squadra), data=oggi(), user_id=session["user_id"])
        db.session.add(nuova)
        db.session.commit()
    return "", 204

@app.route("/verifica/<token>") # Rotta per la verifica della mail in fare di registrazione
def verifica_email(token): 
    email = verifica_token(token)
    if not email:
        return "Token non valido o scaduto.", 400

    utente = User.query.filter_by(email=email).first()
    if not utente:
        return "Utente non trovato.", 404

    if utente.is_verified:
        return "Email già verificata."

    utente.is_verified = True
    db.session.commit()
    return "Email verificata con successo! Ora puoi accedere."

# Configurazione Flask-Mail
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = os.environ.get("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.environ.get("MAIL_PASSWORD")
app.config["MAIL_DEFAULT_SENDER"] = os.environ.get("MAIL_USERNAME")


def invia_email_verifica(destinatario, link_verifica): # Funzione per inviare il messaggio con il link per confermare e terminare la registrazione
    mittente = os.environ.get("MAIL_USERNAME")
    password = os.environ.get("MAIL_PASSWORD")
    server_smtp = "smtp.gmail.com"
    porta = int(os.environ.get("MAIL_PORT", 587))

    corpo = f"""\
Ciao!

Per completare la registrazione, clicca sul seguente link per verificare il tuo indirizzo email:

{link_verifica}

Il link è valido per 1 ora.

Se non hai richiesto questa registrazione, puoi ignorare questa email.
"""

    msg = MIMEText(corpo)
    msg["Subject"] = "Verifica il tuo indirizzo email"
    msg["From"] = mittente
    msg["To"] = destinatario

    try:
        with smtplib.SMTP(server_smtp, porta) as server:
            server.starttls()
            server.login(mittente, password)
            server.send_message(msg)
    except Exception as e:
        print("Errore durante l’invio dell’email:", e)

@app.route("/reset_password", methods=["GET", "POST"]) # Rotta per ripristinare la password
def reset_password():
    if request.method == "POST":
        email = request.form["email"]
        user = User.query.filter_by(email=email).first()
        if user:
            token = genera_token(email)
            link = url_for("nuova_password", token=token, _external=True)
            invia_email_reset(email, link)
            return "Ti abbiamo inviato un'email con il link per reimpostare la password."
        else:
            return "Email non trovata", 404

    return render_template("reset_password.html")

def invia_email_reset(destinatario, link_reset): # Funzione per inviare il messaggio con il link per il ripristino della password
    mittente = os.environ.get("MAIL_USERNAME")
    password = os.environ.get("MAIL_PASSWORD")
    server_smtp = os.environ.get("EMAIL_SMTP", "smtp.gmail.com")
    porta = int(os.environ.get("MAIL_PORT", 587))

    corpo = f"""\
Ciao!

Hai richiesto di reimpostare la tua password. Clicca sul link qui sotto per crearne una nuova:

{link_reset}

Questo link scade tra 1 ora. Se non hai richiesto tu questa operazione, puoi ignorare questa email.
"""

    msg = MIMEText(corpo)
    msg["Subject"] = "Recupero password - Beach Volley"
    msg["From"] = mittente
    msg["To"] = destinatario

    try:
        with smtplib.SMTP(server_smtp, porta) as server:
            server.starttls()
            server.login(mittente, password)
            server.send_message(msg)
    except Exception as e:
        print("Errore durante l’invio dell’email di reset:", e)

@app.route("/nuova-password/<token>", methods=["GET", "POST"]) # Rotta per l'inserimento di una nuova password
def nuova_password(token): 
    email = verifica_token(token)
    if not email:
        return "Il link non è valido o è scaduto.", 400

    utente = User.query.filter_by(email=email).first()
    if not utente:
        return "Utente non trovato.", 404

    if request.method == "POST":
        nuova_pw = request.form["password"]
        if len(nuova_pw) < 6:
            return "La password deve contenere almeno 6 caratteri.", 400

        utente.password_hash = generate_password_hash(nuova_pw)
        db.session.commit()
        return "Password aggiornata con successo! Ora puoi accedere."

    return render_template("nuova_password.html", token=token)

@app.before_request # Rotta per redirect nel caso qualcuno salvi l'indirizzo sbagliato
def blocca_accesso_a_static_root():
    if request.path == "/static":
        return redirect(url_for("login"))


# START
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, host="0.0.0.0", port=3000)
