from flask import Blueprint, render_template
from .models import AuthorizedUser
from . import db

main = Blueprint('main', __name__)

@app.route('/')
def index():
    users = AuthorizedUser.query.all()

    grouped_users = []

    for user in users:
        midweek_entries = []
        weekend_entries = []

        for entry in user.entries:
            day_lower = entry.day.strip().lower()
            if day_lower in ["wed", "thu"]:
                midweek_entries.append(entry)
            elif day_lower in ["sat", "sun"]:
                weekend_entries.append(entry)

        grouped_users.append({
            "user": user,
            "midweek": midweek_entries,
            "weekend": weekend_entries
        })

    return render_template('index.html', users=grouped_users)
