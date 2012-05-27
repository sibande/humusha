from flask import render_template

from zabalaza import app
from apps.dictionary.forms import WordForm, SearchForm

@app.route('/')
def home():
    ctx = {
        'search_form': SearchForm(),
        }
    return render_template('index.html', **ctx)
