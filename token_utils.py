from itsdangerous import URLSafeTimedSerializer
import os

# Segreto usato anche nella app
SECRET_KEY = os.environ.get("SECRET_KEY", "gattopuffy")
serializer = URLSafeTimedSerializer(SECRET_KEY)

def genera_token(email):
    return serializer.dumps(email, salt="email-verifica")

def verifica_token(token, max_age=3600):
    try:
        return serializer.loads(token, salt="email-verifica", max_age=max_age)
    except Exception:
        return None
