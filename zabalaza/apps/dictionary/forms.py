from sqlalchemy import or_

from flask import session
from flaskext.wtf import Form, TextField, Required, SubmitField, \
    ValidationError, SelectField, HiddenField, FieldList, IntegerField


from .models import Word, Part, WordPart, Relation, WordRelation, Language


class UniqueWord(object):
    """This class checks if the word does not exists."""
    def __init__(self, message=None):
        if not message:
            message = u'This word has already been added.'
        self.message = message

    def __call__(self, form, field):
        if Word.query.filter_by(word=field.data).count():
            raise ValidationError(self.message)

class RelationPart(object):
    """This class checks if the specified part can be a word relation."""
    def __init__(self, message=None):
        if not message:
            message = u'This part of speech can not be a relation.'
        self.message = message

    def __call__(self, form, field):
        try:
            part_id = int(field.data)
        except TypeError:
            part_id = None
            
        if not Relation.query.filter_by(part_id=part_id).count():
            raise ValidationError(self.message)


class RelationLimit(object):
    """This class checks if added word relations have not reached the limit."""
    def __init__(self, message=None):
        if not message:
            message = u'The maximum word relations have been reached for this '\
                'word and part of speech.'
        self.message = message

    def __call__(self, form, field):
        try:
            part_id = int(form.part.data)
        except TypeError:
            part_id = None
            
        relation = Relation.query.filter_by(part_id=part_id).first()
        if relation is None:
            raise ValidationError(self.message)

        word_count = WordRelation.query.filter(or_(
            WordRelation.word_id_1==form.word_id_,
            WordRelation.word_id_2==form.word_id_)).\
            filter(WordRelation.relation_id==relation.id).count()
        
        if word_count >= relation.limit and relation.limit:
            raise ValidationError(self.message)


class DynamicSelectField(SelectField):
    def __call__(self, parent_id=None,  **kwargs):
        self.generate_choices(parent_id)

        return super(DynamicSelectField, self).__call__(**kwargs);

    def generate_choices(self, parent_id=None):
        parts = Part.query.filter_by(parent_id=parent_id)
        if parent_id is None:
            parts = parts.filter_by(language_id=session['language'])
        choices = [(p.id, p.label) for p in parts]

        self.choices = choices
        
    

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


class WordRelationForm(Form):
    word = FieldList(TextField(u'Word', validators=[
                Required(), RelationLimit()]))
    word_relation = FieldList(HiddenField(u'Relation', validators=[]))
    part = HiddenField(u'Part', validators=[RelationPart()])
    definition_id = HiddenField(u'Definition ID', validators=[])

    submit = SubmitField(u'Add')
    
    @property
    def word_id(self):
        return self.word_id_

    @word_id.setter
    def word_id(self, value):
        self.word_id_ = value


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
    part = DynamicSelectField(u'Part of speech', choices=[], coerce=int, validators=[
            SpeechTypeUnique()])

    parent_id = HiddenField(u'Parent type ID')
    
    submit = SubmitField(u'Add')

    @property
    def word_id(self):
        return self.word_id_
    
    @word_id.setter
    def word_id(self, value):
        self.word_id_ = value

    def validate(self):
        try:
            parent_id = int(self.parent_id.data)
        except ValueError:
            parent_id = None
        if not parent_id:
            parent_id = None
        parts = Part.query.filter_by(parent_id=parent_id)
        if parent_id is None:
            parts = parts.filter_by(language_id=session['language'])
        choices = [(p.id, p.label) for p in parts]
        self.part.choices = choices

        return super(SpeechPartForm, self).validate();

    # def generate_choices(self, parent_id=None):
    #     self.word_id_ = word_id
    #     choices = [
    #         (p.id, p.label) for p in Part.query.filter_by(parent_id=parent_id)
    #         ]
    #     self.part.choices = choices

