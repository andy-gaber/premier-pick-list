from flask import Flask
import config


app = Flask(__name__)
app.config['SECRET_KEY'] = config.SECRET_KEY

SQLITE_DATABASE_URI = config.SQLITE_DATABASE_URI

from app import api, db