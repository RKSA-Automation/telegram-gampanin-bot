from flask import Flask, render_template
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import AuthorizedUser, SuguanEntry, Base
import os
import logging

# 🔧 Configure Logging
logging.basicConfig(level=logging.DEBUG)  # You can change to INFO in production
logger = logging.getLogger(__name__)

# 🌐 Flask App
app = Flask(__name__)

# 🛠️ Database Configuration
DB_HOST = os.environ.get("DB_HOST", "db")
DB_USER = os.environ.get("DB_USER", "root")
DB_PASS = os.environ.get("DB_PASS", "password")
DB_NAME = os.environ.get("DB_NAME", "suguan_bot")

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}"
engine = create_engine(DATABASE_URL, echo=True)  # `echo=True` shows SQL queries in logs
SessionLocal = sessionmaker(bind=engine)

@app.route("/")
def index():
    session = SessionLocal()
    try:
        users = session.query(AuthorizedUser).all()
        logger.debug(f"Fetched {len(users)} authorized users from DB.")
        return render_template("index.html", users=users)
    except Exception as e:
        logger.error(f"❌ Error fetching users: {e}")
        return "Internal Server Error", 500
    finally:
        session.close()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
