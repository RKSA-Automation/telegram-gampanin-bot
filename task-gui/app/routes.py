from flask import Blueprint, render_template
from .models import AuthorizedUser, TaskAssignment
from . import db

main = Blueprint('main', __name__)

@main.route('/')
def index():
    users = AuthorizedUser.query.all()
    return render_template('index.html', users=users)
