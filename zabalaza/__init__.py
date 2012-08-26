
import string

from flask import Flask, session, request_started

from flask_sqlalchemy import SQLAlchemy, Session
from flaskext.babel import gettext, ngettext, lazy_gettext
from flaskext.babel import Babel

from flask_debugtoolbar import DebugToolbarExtension

from zabalaza.utils.history_meta import versioned_session

app = Flask(__name__)

babel = Babel(app)

app.secret_key = '\xbb#\xbb\x1b\x91\x15\xd6\xf7\xc7~\xa18\x08D\xed\xc37$,\x10\xc6\x8b\xbf\xa2'
# Debug
# app.debug = True
# toolbar = DebugToolbarExtension(app)

# SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://root:' + \
    open('db.passwd', 'r').read().strip()+'@localhost/zabalaza'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)
# Model versioning
versioned_session(Session)

# Templates
app.jinja_env.add_extension('jinja2.ext.i18n')
app.jinja_env.add_extension('jinja2.ext.loopcontrols')
app.jinja_env.install_gettext_callables(gettext, ngettext, newstyle=True)

def datetimeformat(value, format='%Y-%m-%d at %H:%M'):
    from babel.dates import format_date, format_datetime, format_time
    return format_datetime(value, locale='en_US')

app.jinja_env.filters['datetimeformat'] = datetimeformat

# Views
import zabalaza.views

from zabalaza.apps.words.models import Language, Word
from zabalaza.apps.words.forms import SearchForm
from apps.words.views import words as words

# Blueprints
app.register_blueprint(words, url_prefix='/words')


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


def latest_words(value, count=4):
    print dir(Word)
    words = Word.query.filter(Word.language_id==int(value))\
        .order_by('word.id DESC').limit(count)
    return words
app.jinja_env.filters['latest_words'] = latest_words

@app.context_processor
def _template_ctx_languages():
    return dict(
        languages=Language.query.all(),
        ascii_letters=list(string.ascii_lowercase),
        search_form=SearchForm(),
    )


@babel.localeselector
def get_locale():
    return session['languages'].get(session['app_language'], 'en')

@app.errorhandler(404)
def page_not_found(error):
    return gettext(u'This page does not exist {0}'.format(404))

