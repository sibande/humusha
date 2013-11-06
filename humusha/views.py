from flask import render_template, session, request, redirect, flash

from flask_babel import gettext, ngettext, lazy_gettext as _
from humusha import app
from apps.words.forms import WordForm, SearchForm
from apps.words.models import Language, Word

@app.route('/')
def home():
    word = Word()
    featured_words = word.main_featured(4, 0)

    ctx = {
        'form': SearchForm(),
        'featured_words': featured_words,
    }
    return render_template('index.html', **ctx)



@app.route('/switch/<language_type>/<language_code>', methods=['GET'])
def switch_language(language_type, language_code):
    def _switch_langauge(message = None):
        language = Language.query.filter(Language.code==language_code).first()
        if language is not None:
            session[language_type] = language.id
            flash(gettext(u'Language changed to {0}')\
                      .format(language.label), 'success')

    if language_type in ['app_language', 'language']:
        _switch_langauge()

    return redirect(request.args.get('next', '/'))
