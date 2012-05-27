from flask import render_template, flash, request, redirect, url_for, abort
from werkzeug.datastructures import MultiDict

from zabalaza import app, db

from .forms import WordForm, SearchForm, SpeechPartForm, DefinitionForm, \
    UsageForm
from .models import Word, WordPart, Definition, Usage, Part


@app.route('/words/')
def words():
    words = Word.query.order_by('created DESC').limit(600).all()
    ctx = {
        'words': words,
        'search_form': SearchForm(),
        }
    return render_template('dictionary/words.html', **ctx)


@app.route('/words/<word_data>', methods=['GET', 'POST'])
def view_word(word_data):
    word = Word.query.filter_by(word = word_data).first()
    if word is None:
        abort(404)

    
    speech_parts = WordPart.query.filter_by(word_id=word.id)
    
    words = Word.query.filter(Word.word.like('%{0}%'.format(word_data)))

    ctx = {
        'word': word,
        'speech_parts': speech_parts,
        'words': words,
        'search_form': SearchForm(),
        }
    return render_template('dictionary/view_word.html', **ctx)


@app.route('/words/edit/<word_data>/', methods=['GET', 'POST'])
@app.route('/words/edit/<word_data>/d<int:definition_data>', methods=['GET', 'POST'])
def edit_word(word_data, definition_data=None):
    word = Word.query.filter_by(word = word_data).first()
    if word_data is None:
        pass
    speech_parts = WordPart.query.filter_by(word_id=word.id)
    
    speech_part_form = SpeechPartForm()
    speech_part_form.generate_choices(word.id)
    definition_form = DefinitionForm()
    usage_form = UsageForm()

    words = Word.query.filter(Word.word.like('%{0}%'.format(word_data)))

    if speech_part_form.validate_on_submit():
        word_part = WordPart(word.id, speech_part_form.part.data)
        db.session.add(word_part)
        db.session.commit()
        flash(u'The word has been associated with the part of speech.', 'success')
        
    ctx = {
        'word': word,
        'speech_parts': speech_parts,
        'usage_form': usage_form,
        'words': words,
        'definition_form': definition_form,
        'speech_part_form': speech_part_form,
        'search_form': SearchForm(),
        }
    return render_template('dictionary/edit_word.html', **ctx)


@app.route('/words/add_definition/<word_data>', methods=['POST'])
def add_definition(word_data):
    definition_form = DefinitionForm(csrf_enabled=False)
    usage_form = UsageForm(csrf_enabled=False)

    if definition_form.validate_on_submit() and usage_form.validate_on_submit():
        
        definition_data = definition_form.definition.data
        definition_id_data = definition_form.definition_id.data
        part_id_data = definition_form.part.data
        sentences_data = usage_form.sentence.data
        sentences_id_data = usage_form.sentence_id.data

        part = Part.query.filter_by(id=part_id_data).first()
        word = Word.query.filter_by(word=word_data).first()
    
        try:
            definition_id_data = int(definition_id_data)
            definition = Definition.query.filter_by(id=definition_id_data).first()
        except (ValueError, TypeError):
            definition = None

        if definition_data and word is not None:
            if definition is not None:
                definition.definition=definition_data
            else:
                definition = Definition(
                    definition=definition_data,
                    word_id=word.id,
                    part_id=part_id_data)
            db.session.add(definition)
            db.session.commit()
            for sentence_index, sentence_data in enumerate(sentences_data):
                
                if not sentence_index > len(sentences_id_data)-1:
                    usage = Usage.query.filter_by(
                        id=sentences_id_data[sentence_index]).first()
                else:
                    usage = None
                if usage is not None:
                    if not sentence_data:
                        db.session.delete(usage)
                    else:
                        usage.sentence=sentence_data
                        db.session.add(usage)
                else:
                    if not sentence_data:
                        continue
                    usage = Usage(sentence=sentence_data,
                                  definition_id=definition.id)
                    db.session.add(usage)
            db.session.commit()
            flash(u'Definition added.', 'success')
        else:
            flash(u'Definition not added.', 'error')
    else:
        flash(u'Definition not added.', 'error')

    return redirect(url_for('edit_word', word_data=word_data))



@app.route('/words/add', methods=['GET', 'POST'])
def add_words(form_class=WordForm):
    form = form_class()

    if form.validate_on_submit():
        word = Word(form.word.data)
        db.session.add(word)
        db.session.commit()
        # Clear form
        form = form_class(MultiDict())
        flash(u'The word sucessfully added.', 'success')
    else:
        if request.method == 'POST':
            flash(u'Error while trying to save the word.', 'error')

    words = Word.query.order_by('created DESC').limit(600).all()

    ctx = {
        'form': form,
        'words': words,
        'search_form': SearchForm(),
        }
    
    return render_template('dictionary/add_words.html', **ctx)

@app.route('/words/search', methods=['GET', 'POST'])
def search_words(form_class=SearchForm):
    form = form_class()

    words = Word.query.order_by('created DESC').limit(600).all()

    if form.validate_on_submit() or request.args.get('q'):
        if request.args.get('q') and not form.word.data:
            word_data = request.args.get('q')
            form = form_class(MultiDict({'word':word_data}))
        else:
            word_data = form.word.data
        word = Word.query.filter_by(word = word_data).first()
        if word is not None:
            return redirect(url_for('view_word', word_data=word_data))
        words = Word.query.filter(Word.word.like('%{0}%'.format(word_data)))
    else:
        if request.method == 'POST':
            flash(u'Please enter the word you are looking for.', 'error')

    ctx = {
        'form': form,
        'words': words,
        'search_form': form,
        }
    
    return render_template('dictionary/search_words.html', **ctx)
