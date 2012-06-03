from flask import Flask
from flask_sqlalchemy import SQLAlchemy, Session

from zabalaza.utils.history_meta import versioned_session


app = Flask(__name__)

app.secret_key = '\xbb#\xbb\x1b\x91\x15\xd6\xf7\xc7~\xa18\x08D\xed\xc37$,\x10\xc6\x8b\xbf\xa2'

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://root:' + \
    open('db.passwd', 'r').read()+'@localhost/zabalaza'
app.config['SQLALCHEMY_ECHO'] = True

db = SQLAlchemy(app)


import zabalaza.views
import zabalaza.apps.dictionary.views


@app.errorhandler(404)
def page_not_found(error):
    return 'This page does not exist', 404


versioned_session(Session)
