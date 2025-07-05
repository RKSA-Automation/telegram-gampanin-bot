from flask import Flask, render_template
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, joinedload
from models import AuthorizedUser, SuguanEntry
import os
import logging

app = Flask(__name__)

logging.basicConfig(level=logging.DEBUG)

DB_HOST = os.environ.get("DB_HOST", "db")
DB_USER = os.environ.get("DB_USER", "root")
DB_PASS = os.environ.get("DB_PASS", "password")
DB_NAME = os.environ.get("DB_NAME", "suguan_bot")

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}"
engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(bind=engine)

@app.route("/")
def index():
    session = SessionLocal()
    try:
        users = session.query(AuthorizedUser).options(joinedload(AuthorizedUser.entries)).all()
        grouped_users = []

        for user in users:
            midweek = []
            weekend = []

            for entry in user.entries:
                day = entry.day.strip().lower()
                if day in ['wed', 'thu']:
                    midweek.append(entry)
                elif day in ['sat', 'sun']:
                    weekend.append(entry)

            grouped_users.append({
                "full_name": user.full_name,
                "midweek": midweek,
                "weekend": weekend
            })

        return render_template("index.html", users=grouped_users)

    except Exception as e:
        logging.error(f"❌ Error fetching users: {e}")
        return "Internal Server Error", 500
    finally:
        session.close()
