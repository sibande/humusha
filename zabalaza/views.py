from flask import render_template, session, request, redirect, flash

from flaskext.babel import gettext, ngettext, lazy_gettext as _
from zabalaza import app
from apps.words.forms import WordForm, SearchForm
from apps.words.models import Language

@app.route('/')
def home():
    ctx = {
        'form': SearchForm(),
    }
    return render_template('index.html', **ctx)



@app.route('/switch/language', methods=['POST'])
def switch_language():
    def _switch_langauge(langauge_type, message = None):
        language_data = request.form.get(langauge_type, None)
        language = Language.query.filter(Language.code==language_data).first()
        if language is not None:
            session[langauge_type] = language.id
            flash(gettext(u'Language changed to {0}')\
                      .format(language.label), 'success')

    for language_type in ['app_language', 'language']:
        _switch_langauge(language_type)

    return redirect(request.args.get('next', '/'))
