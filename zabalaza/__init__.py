from flask import Flask, session, request_started
from flask_sqlalchemy import SQLAlchemy, Session
from flaskext.babel import gettext, ngettext, lazy_gettext
from flaskext.babel import Babel


from zabalaza.utils.history_meta import versioned_session


app = Flask(__name__)
babel = Babel(app)

app.secret_key = '\xbb#\xbb\x1b\x91\x15\xd6\xf7\xc7~\xa18\x08D\xed\xc37$,\x10\xc6\x8b\xbf\xa2'

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://root:' + \
    open('db.passwd', 'r').read()+'@localhost/zabalaza'
app.config['SQLALCHEMY_ECHO'] = True

db = SQLAlchemy(app)
versioned_session(Session)

app.jinja_env.add_extension('jinja2.ext.i18n')
app.jinja_env.install_gettext_callables(gettext, ngettext, newstyle=True)

import zabalaza.views
import zabalaza.apps.dictionary.views
from zabalaza.apps.dictionary.models import Language

def _set_default_language(app):
    if 'app_language' not in session:
        language = Language.query.filter(Language.code=='en').first()
        if language is None:
            session['app_language'] = 1
            session['language'] = 1
        else:
            session['app_language'] = language.id
            session['language'] = language.id
        session['languages'] = dict((l.id, l.code) for l in Language.query.all())
request_started.connect(_set_default_language, app)

@app.context_processor
def _template_ctx_languages():
    return dict(languages=Language.query.all())


@babel.localeselector
def get_locale():
    return session['languages'].get(session['app_language'], 'en')

@app.errorhandler(404)
def page_not_found(error):
    return gettext(u'This page does not exist', 404)

