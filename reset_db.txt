from app import db, app
from sqlalchemy import text

with app.app_context():
    try:
        db.session.execute(text('DROP TABLE "user" CASCADE;'))  # ⚠️ virgolette obbligatorie!
        db.session.commit()
        print("Tabella 'user' eliminata con successo.")
    except Exception as e:
        print(f"Errore durante il DROP: {e}")
    
    db.create_all()
    print("Tabelle rigenerate.")
