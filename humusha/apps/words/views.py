from flask import render_template, flash, request, redirect, url_for, abort,\
    session, Blueprint
from werkzeug.datastructures import MultiDict
from flask_babel import gettext, ngettext, lazy_gettext as _

from humusha.utils.pagination import Pagination
from humusha import db

from .forms import WordForm, SearchForm, SpeechPartForm, DefinitionForm, \
    UsageForm, WordRelationForm, TranslationForm
from .models import Word, WordPart, Definition, Usage, Part, Relation,\
    WordRelation, Translation, Language, Change


words = Blueprint('words', __name__)

PER_PAGE = 80

@words.route('/')
@words.route('/<language_code>/', methods=['GET', 'POST'])
def index(language_code=None):
    page = request.args.get('page', 1)
    try:
        page = int(page)
        if page < 1:
            page = 1
    except ValueError:
        page = 1
    
    words = Word.query.order_by('word.id DESC')\
        .slice((page - 1)*PER_PAGE, page*PER_PAGE).all()

    words_count = Word.query.order_by('word.id DESC').count()
    pagination = Pagination(page, PER_PAGE, words_count)

    ctx = {
        'words': words,
        'pagination': pagination,
    }
    return render_template('words/words.html', **ctx)

@words.route('/browse/<starts_with>/')
@words.route('/browse/<starts_with>/<language_code>/', methods=['GET', 'POST'])
def browse(starts_with, language_code=None):
    page = request.args.get('page', 1)
    try:
        page = int(page)
        if page < 1:
            page = 1
    except ValueError:
        page = 1

    words = Word.query.filter(Word.word.startswith(starts_with))\
        .order_by('word.id DESC').slice((page - 1)*PER_PAGE, page*PER_PAGE).all()
    words_count = Word.query.filter(Word.word.startswith(starts_with)).count()
    pagination = Pagination(page, PER_PAGE, words_count)
        
    ctx = {
        'words': words,
        'pagination': pagination,
    }
    return render_template('words/browse.html', **ctx)


@words.route('/<word_data>', methods=['GET', 'POST'])
@words.route('/<language_code>/<word_data>', methods=['GET', 'POST'])
def view(word_data, language_code=None):
    word = Word.get_word(word_data, language_code)
    if word is None:
        abort(404)
    speech_parts = WordPart.query.join('part').filter(WordPart.word_id==word.id)\
        .filter(Part.parent_id==None)
    
    words = Word.query.filter(Word.word.like('%{0}%'.format(word_data)))
    thesaurus_parts = Part.thesaurus_parts(word.language_id)
    translation_part = Part.translation_part(word.language_id)

    ctx = {
        'word': word,
        'speech_parts': speech_parts,
        'words': words,
        'thesaurus_parts': thesaurus_parts,
        'translation_part': translation_part,
    }
    return render_template('words/view_word.html', **ctx)


@words.route('/<language_code>/edit/<word_data>/', methods=['GET', 'POST'])
@words.route('/<language_code>/edit/<word_data>/p<int:part_data>', methods=['GET', 'POST'])
@words.route('/<language_code>/edit/<word_data>/d<int:definition_data>', methods=['GET', 'POST'])
def edit(word_data, definition_data=None, part_data=None, language_code=None):
    word = Word.get_word(word_data, language_code)
    if word is None:
        abort(404)

    speech_parts = WordPart.query.join('part').filter(WordPart.word_id==word.id)\
        .filter(Part.parent_id == None)
    thesaurus_parts = Part.thesaurus_parts(word.language_id)

    translation_part = Part.translation_part(word.language_id)

    speech_part_form = SpeechPartForm()

    speech_part_form.word_id = word.id
    # speech_part_form.set_word(word.id)

    definition_form = DefinitionForm()
    usage_form = UsageForm()
    word_relation_form = WordRelationForm()
    translation_form = TranslationForm()
    translation_form.language_choices()

    words = Word.query.filter(Word.word.like('%{0}%'.format(word_data)))

    if speech_part_form.validate_on_submit():
        word_part = WordPart(word.id, speech_part_form.part.data)
        db.session.add(word_part)
        db.session.commit()
        flash(gettext(u'The word has been associated with the part of speech.'), 'success')
        
    ctx = {
        'word': word,
        'speech_parts': speech_parts,
        'usage_form': usage_form,
        'thesaurus_parts': thesaurus_parts,
        'translation_part': translation_part,
        'words': words,
        'word_relation_form': word_relation_form,
        'definition_form': definition_form,
        'speech_part_form': speech_part_form,
        'translation_form': translation_form,
    }
    return render_template('words/edit_word.html', **ctx)


@words.route('/<language_code>/add_definition/<word_data>', methods=['POST'])
def add_definition(word_data, language_code=None):
    word = Word.get_word(word_data, language_code)
    if word is None:
        abort(404)
    definition_form = DefinitionForm(csrf_enabled=False)
    usage_form = UsageForm(csrf_enabled=False)

    if definition_form.validate_on_submit() and usage_form.validate_on_submit():
        definition_data = definition_form.definition.data
        definition_id_data = definition_form.definition_id.data
        part_id_data = definition_form.part.data
        sentences_data = usage_form.sentence.data
        sentences_id_data = usage_form.sentence_id.data
        try:
            translation_id_data = int(definition_form.translation_id.data)
        except ValueError:
            translation_id_data = None

        part = Part.query.filter_by(id=part_id_data).first()
    
        try:
            definition_id_data = int(definition_id_data)
            definition = Definition.query.filter_by(id=definition_id_data).first()
        except ValueError:
            definition = None

        if definition_data and word is not None:
            if definition is not None:
                definition.definition=definition_data
            else:
                definition = Definition(
                    definition=definition_data,
                    word_id=word.id,
                    part_id=part_id_data)
                definition.translation_id = translation_id_data
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
            flash(gettext(u'Definition added.'), 'success')
        else:
            flash(gettext(u'Definition not added.'), 'error')
    else:
        flash(gettext(u'Definition not added.'), 'error')

    return redirect(url_for('words.edit', language_code=language_code, word_data=word_data))


@words.route('/<language_code>/edit/relation/<word_data>', methods=['POST'])
def relation(word_data, language_code=None, form_class = WordRelationForm):
    word_relation_form = form_class()
    
    word_1 = Word.get_word(word_data, language_code)
    if word_1 is None:
        return redirect(url_for('words.edit', language_code=language_code, word_data=word_data))

    word_relation_form.word_id = word_1.id

    validates = word_relation_form.validate_on_submit()
    
    word_relation = None
    for word_index, word_data_2 in enumerate(word_relation_form.word.data):
        word_relation = None
        try:
            part_data = int(word_relation_form.part.data)
        except ValueError:
            part_data = None
        relation = Relation.query.filter(Relation.part_id==part_data).first()
        try:
            translation_id_data = int(word_relation_form.translation_id.data)
            translation = Translation.query\
                .filter(Translation.id==translation_id_data).first()
            language_id = translation.language_id
        except ValueError:
            translation_id_data = None
            translation = None
            language_id = word_1.language_id
        try:
            definition_id_data = int(word_relation_form.definition_id.data)
        except ValueError:
            definition_id_data = None

        if word_index < len(word_relation_form.word_relation.data): # Update
            word_relation_data = int(word_relation_form.word_relation.data[word_index])
        elif not validates: # Relation limit reached
            continue
        else: # New word relation
            word_relation_data = None

        word_2 = Word.query.filter(Word.word==word_data_2)\
            .filter(Word.language_id==language_id).first()

        if word_2 is None:
            word_2 = Word(word=word_data_2, language_id=language_id)
            db.session.add(word_2)
            db.session.commit()
            flash(gettext(u'Relation word was added.'), 'success')
        
        if word_relation_data is not None:
             word_relation = WordRelation.query\
                .filter(WordRelation.translation_id==translation_id_data)\
                .filter(WordRelation.relation_id==relation.id)\
                .filter(WordRelation.id==word_relation_data).first()
             if word_relation is None:
                 continue
        else:
            word_relation = WordRelation.query\
                .filter(WordRelation.translation_id==translation_id_data)\
                .filter(WordRelation.word_id_1==word_1.id)\
                .filter(WordRelation.word_id_2==word_2.id)\
                .filter(WordRelation.relation_id==relation.id)\
                .filter(WordRelation.definition_id==definition_id_data).first()
            if word_relation is not None:
                flash(gettext(u'The relationship was rejected.'), 'error')
                continue

        if word_relation is not None:
            word_relation.word_id_1=word_1.id
            word_relation.word_id_2=word_2.id
            word_relation.definition_id = definition_id_data
        elif validates:
            word_relation = WordRelation(
                word_id_1=word_1.id, word_id_2=word_2.id, relation_id=relation.id,
            )
            word_relation.translation_id = translation_id_data
            word_relation.definition_id = definition_id_data
            
        if word_relation is not None:
            flash(gettext(u'Word is now related to the specified word.'), 'success')
            db.session.add(word_relation)
            db.session.commit()
        else:
            flash(gettext(u'The relationship was rejected.'), 'error')
    else:
        if not word_relation_form.word.data:
            flash(gettext(u'The relationship was rejected.'), 'error')
    if word_relation is None:
        flash(gettext(u'The relationship was rejected.'), 'error')

    return redirect(url_for('words.edit', language_code=language_code, word_data=word_data))


@words.route('/<language_code>/translation/language/<word_data>', methods=['POST'])
def translation_language(word_data, language_code=None):
    form = TranslationForm(csrf_enabled=False)
    form.language_choices()

    word = Word.get_word(word_data, language_code)
    if word is None:
        return redirect(url_for('words.edit', language_code=language_code, word_data=word_data))
    if form.validate_on_submit():
        try:
            part_id_data = int(form.part_id.data)
        except ValueError:
            part_id_data = None
        language_id_data = int(form.language_id.data)
        translation = Translation(
            part_id = part_id_data,
            word_id = word.id,
            language_id = language_id_data
        )
        db.session.add(translation)
        db.session.commit()
        flash(gettext(u'The language has been sucessfully added for translation.'), 'success')
    else:
        flash(gettext(u'The language has been already added for translation.'), 'error')
    return redirect(url_for('words.edit', language_code=language_code, word_data=word_data))


@words.route('/add', methods=['GET', 'POST'])
def add(form_class=WordForm):
    page = request.args.get('page', 1)
    try:
        page = int(page)
        if page < 1:
            page = 1
    except ValueError:
        page = 1

    form = form_class()

    if form.validate_on_submit():
        word = Word(form.word.data, session['language'])
        db.session.add(word)
        db.session.commit()
        # Clear form
        form = form_class(MultiDict())
        flash(gettext(u'The word sucessfully added.'), 'success')
    else:
        if request.method == 'POST':
            flash(gettext(u'Error while trying to save the word.'), 'error')

    words = Word.query.order_by('word.id DESC')\
                      .slice((page - 1)*PER_PAGE, page*PER_PAGE).all()
    words_count = Word.query.order_by('word.id DESC').count()
    pagination = Pagination(page, PER_PAGE, words_count)

    ctx = {
        'form': form,
        'words': words,
        'pagination': pagination,
    }
    
    return render_template('words/add_words.html', **ctx)


@words.route('/<language_code>/history/<word_data>')
def history(word_data, language_code=None):
    word = Word.get_word(word_data, language_code)
    if word is None:
        abort(404)
    revisions = Change.word_revisions(word.id)

    ctx = {
        'search_form': SearchForm(),
        'word': word,
        'revisions': revisions,
    }
    
    return render_template('words/history.html', **ctx)


@words.route('/search', methods=['GET', 'POST'])
def search(form_class=SearchForm):
    page = request.args.get('page', 1)
    try:
        page = int(page)
        if page < 1:
            page = 1
    except ValueError:
        page = 1

    form = form_class()

    words = Word.query.order_by('word.id DESC')\
                      .slice((page - 1)*PER_PAGE, page*PER_PAGE).all()
    words_count = Word.query.order_by('word.id DESC').count()

    if form.validate_on_submit() or request.args.get('q'):
        if request.args.get('q') and not form.word.data:
            word_data = request.args.get('q')
            form = form_class(MultiDict({'word':word_data}))
        else:
            word_data = form.word.data
        word = Word.query.filter_by(word = word_data).first()
        if word is not None:
            return redirect(url_for('words.view',
                                    language_code=word.language.code,
                                    word_data=word_data))
        words = Word.query.filter(Word.word.like('%{0}%'.format(word_data)))
        words_count = words.count()
        words = words.slice((page - 1)*PER_PAGE, page*PER_PAGE)

    else:
        if request.method == 'POST':
            flash(gettext(u'Please enter the word you are looking for.'), 'error')
            

    pagination = Pagination(page, PER_PAGE, words_count)

    ctx = {
        'form': form,
        'words': words,
        'search_form': form,
        'pagination': pagination,
    }
    
    return render_template('words/search_words.html', **ctx)


@words.route('/statistics', methods=['GET', 'POST'])
def statistics():
    ctx = {
    }

    return render_template('words/statistics.html', **ctx)
