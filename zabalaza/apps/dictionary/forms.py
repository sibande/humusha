from flaskext.wtf import Form, TextField, Required, SubmitField, \
    ValidationError, SelectField, HiddenField, FieldList


from .models import Word, Part, WordPart


class UniqueWord(object):
    """This class checks if the word does not exists."""
    def __init__(self, message=None):
        if not message:
            message = u'This word has already been added.'
        self.message = message

    def __call__(self, form, field):
        if Word.query.filter_by(word=field.data).count():
            raise ValidationError(self.message)


class SpeechTypeUnique(object):
    """This class checks if the word has been not been assigned to selected 
    type of speech.
    
    """
    def __init__(self, message=None):
        if not message:
            message = u'The selected type of speech is already associated with this word.'
        self.message = message

    def __call__(self, form, field):
        if WordPart.query.filter_by(part_id=field.data,
                                    word_id=form.word_id_).count():
            raise ValidationError(self.message)


class WordForm(Form):
    word = TextField(u'Word', validators=[
            Required(), UniqueWord()])
    submit = SubmitField(u'Add')

class DefinitionForm(Form):
    definition = TextField(u'Definition', validators=[])
    
    part = HiddenField(u'Part', validators=[])
    definition_id = HiddenField(u'Definition ID', validators=[])

    submit = SubmitField(u'Define')

class UsageForm(Form):
    sentence = FieldList(TextField(u'Usage examples', []), min_entries=0)
    # sentence = FieldList(TextField(u'Usage examples', validators=[]))
    sentence_id = FieldList(HiddenField(u'Usage ID', validators=[]))
    submit = SubmitField(u'Add')


class SearchForm(Form):
    word = TextField(u'Word', validators=[Required()])
    submit = SubmitField(u'Search')


class SpeechPartForm(Form):
    part = SelectField(u'Part of speech', choices=[], coerce=int, validators=[
            SpeechTypeUnique()])
    submit = SubmitField(u'Add')

    def generate_choices(self, word_id=None, parent_id=None):
        self.word_id_ = word_id
        choices = [
            (p.id, p.label) for p in Part.query.filter_by(parent_id=parent_id)
            ]
        self.part.choices = choices

