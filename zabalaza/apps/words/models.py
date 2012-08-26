import datetime
from sqlalchemy import or_
from sqlalchemy.orm import aliased, joinedload, mapper
from sqlalchemy.sql import func
from flask import session, url_for
from jinja2 import Markup

from zabalaza import db

from zabalaza.utils.history_meta import Versioned, versioned_session


class Language(Versioned, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(1000))
    label = db.Column(db.String(1000))
    code = db.Column(db.String(20))
    
    def __init__(self, name=None, label=None, code=None):
        self.name = name
        self.code = code
        self.label = label

    @property
    def dependant_word_id(self):
        return None

    def __unicode__(self):
        return u'{0}'.format(self.label)

    def __repr__(self):
        return '<Language {0} ({1})>'.format(self.name, self.code)


class Word(Versioned, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(1000))
    language_id = db.Column(db.Integer, db.ForeignKey('language.id'))

    language = db.relationship("Language", lazy="joined")

    def __init__(self, word=None, language_id=None):
        self.word = word
        self.language_id = language_id

    def definitions(self, part_id=None, translation_id=None, limit=None):
        definitions = Definition.query\
            .filter(Definition.translation_id==translation_id)\
            .filter(Definition.word_id==self.id)
        if part_id is not None:
            definitions = definitions.filter(Definition.part_id==part_id)
        else:
            definitions = definitions.filter(Definition.word_id==self.id)
        if limit is not None:
            print 'helllo  world'
            print limit
            definitions = definitions.limit(limit)
        return definitions

    @staticmethod
    def get_word(word_data, language_code):
        word = Word.query.filter_by(word = word_data)
        if language_code is not None:
            word = word.join('language').filter(Language.code==language_code)
        return word.first()

    def relations(self, part_id, definition_id=None, translation_id=None):
        relation = Relation.query.filter(Relation.part_id==part_id).first()
        if relation is None:
            return []
        word_relations = WordRelation.query\
            .filter(WordRelation.relation_id==relation.id)\
            .filter(WordRelation.translation_id==translation_id)\
            .filter(WordRelation.definition_id==definition_id)
        if relation.bidirectional:
            word_relations = word_relations.filter(
                or_(WordRelation.word_id_1==self.id, WordRelation.word_id_2==self.id)
            )
        else:
            word_relations = word_relations.filter(WordRelation.word_id_1==self.id)
        return word_relations

    def featured(self, language_id=None, limit=2, min_count=2):
        words = db.session.query(Definition.word_id).join(Definition.word)\
            .join(Definition.usage_examples)\
            .filter(Word.language_id==language_id)\
            .group_by(Definition.word_id)\
            .having(func.count(Definition.word_id) > min_count)\
            .having(func.count(Usage.id) > min_count).limit(limit)
        _words = list()
        for word_id in words:
            word = Word.query.filter_by(id=word_id[0]).first()
            _words.append(word)
        return _words
    
    def main_featured(self, limit=2, min_count=2):
        """Gets featured words for the homepage carousel"""
        _featured = dict()
        if 'languages' not in session:
            print 'hello world'
            return _featured
        for language_id, label in session['languages'].items():
            words = self.featured(language_id, limit, min_count)
            _featured[language_id] = words
        return _featured
    
    @property
    def dependant_word_id(self):
        return self.id

    def __unicode__(self):
        language = Language.query.filter(Language.id==self.language_id).first()
        markup = Markup(u'<a href="{0}">{1}</a>').format(
            url_for(
                'words.view', word_data=self.word, language_code=language.code
            ), self.word)
        return markup 
        
    def __repr__(self):
        return '<Word %r>' % self.word


class Part(Versioned, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(1000))
    label = db.Column(db.String(1000))
    parent_id = db.Column(db.Integer, db.ForeignKey('part.id'))
    language_id = db.Column(db.Integer, db.ForeignKey('language.id'))

    parent = db.relationship("Part", remote_side=[id])
    
    def __init__(self, name=None, label=None, parent_id=None):
        self.name = name
        self.label = label
        self.parent_id = parent_id
    
    @staticmethod
    def thesaurus_parts(language_id):
        parent_part = aliased(Part)
        parts = Part.query.join(parent_part, Part.parent)\
            .filter(Part.parent_id == parent_part.id)\
            .filter(parent_part.name=='thesaurus')\
            .filter(parent_part.language_id==language_id)
        return parts

    @staticmethod
    def translation_part(language_id):
        part = Part.query.filter(Part.name=='translation')\
            .filter(Part.language_id==language_id).first()
        return part
    
    def dependants_exist(self):
        definitions = Definition.query.filter(Definition.part_id==self.id).count()
        if definitions:
            return True
        word_relations  = WordRelation.query.join('relation')\
            .filter(Relation.part_id==self.id).count()
        return word_relations > 0

    @property
    def dependant_word_id(self):
        return None

    def translation_languages(self, word_id):
        languages = Translation.query.filter(Translation.part_id==self.id)\
            .filter(Translation.word_id==word_id)
        return languages

    def __unicode__(self):
        return u'{0}'.format(self.label)

    def __repr__(self):
        return '<Part of speech %r>' % self.label


class Definition(Versioned, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    definition = db.Column(db.Text)
    word_id = db.Column(db.Integer, db.ForeignKey('word.id'))
    part_id = db.Column(db.Integer, db.ForeignKey('part.id'))
    translation_id = db.Column(db.Integer, db.ForeignKey('translation.id'),
                               default=None)

    word = db.relationship("Word")
    part = db.relationship("Part")

    def __init__(self, definition=None, word_id=None,
                 part_id=None):
        self.definition = definition
        self.word_id = word_id
        self.part_id = part_id

    @property
    def dependant_word_id(self):
        return self.word_id

    def __unicode__(self):
        return u'{0}'.format(self.definition)

    def __repr__(self):
        return '<Definition %r>' % self.definition


class Etymology(Versioned, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    word_id = db.Column(db.Integer, db.ForeignKey('word.id'))
    etymology = db.Column(db.Text)
    
    def __init__(self, word_id=None, etymology=None):
        self.word_id = word_id
        self.etymology = etymology

    @property
    def dependant_word_id(self):
        return self.word_id

    def __unicode__(self):
        return u'{0}'.format(self.etymology)
        
    def __repr__(self):
        return '<Etymology %r>' % self.etymology[0:50]


class Change(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    word_id = db.Column(db.Integer, db.ForeignKey('word.id'), default=None)
    version = db.Column(db.Integer)
    row_id = db.Column(db.Integer)
    model = db.Column(db.String(1000))
    action = db.Column(db.String(1000))
    created = db.Column(db.DateTime(timezone=True), default=datetime.datetime.now)
    
    def __init__(self, row_id=None, word_id=None, version=None,
                 model=None, action=None):
        self.row_id = row_id
        self.word_id = word_id
        self.version = version
        self.model = model
        self.action = action

    @property
    def prev_revision(self):
        revision = Change.query.filter(Change.row_id==self.row_id)\
            .filter(Change.word_id==self.word_id)\
            .filter(Change.version==self.version-1)\
            .filter(Change.model==self.model).first()
        return revision

    def history_object(self):
        """The revision model object from the history table or model
        (eg. WordHistory, PartHistory ...)"""
        history_mapper = globals()[self.model].__history_mapper__
        history_cls = history_mapper.class_
        
        history_obj = history_cls.query.filter_by(id=self.row_id)\
            .filter_by(version=self.version).first()

        return history_obj
        
    @staticmethod
    def word_revisions(word_id):
        """Gets all changes of objects that have this word_id as a dependant"""
        revisions = Change.query.filter(Change.word_id==word_id)\
            .order_by("change.created DESC")
        return revisions
        
    def __repr__(self):
        return '<Change %r>' % self.word_id



class Usage(Versioned, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    definition_id = db.Column(db.Integer, db.ForeignKey('definition.id'))
    sentence = db.Column(db.Text)
    
    definition = db.relationship("Definition")
    
    def __init__(self, sentence=None, definition_id=None):
        self.sentence = sentence
        self.definition_id = definition_id

    @property
    def dependant_word_id(self):
        # self.definition?
        definition = Definition.query\
            .filter(Definition.id==self.definition_id).first()
        return definition.dependant_word_id

    def __unicode__(self):
        return u'{0}'.format(self.sentence)
        
    def __repr__(self):
        return '<Sentence %r>' % self.definition_id

Definition.usage_examples = db.relationship('Usage')


class WordPart(Versioned, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    word_id = db.Column(db.Integer, db.ForeignKey('word.id'),
                        primary_key=True)
    part_id = db.Column(db.Integer, db.ForeignKey('part.id'),
                        primary_key=True)
    
    word = db.relationship("Word", lazy="joined")
    part = db.relationship("Part", lazy="joined")

    def __init__(self, word_id=None, part_id=None):
        self.word_id = word_id
        self.part_id = part_id

    @property
    def dependant_word_id(self):
        return self.word_id

    @property
    def part_types(self):
        return self.query.join(Part).filter(Part.parent_id==self.part_id)\
            .filter('word_part.word_id={0}'.format(self.word_id))

    def __unicode__(self):
        word_history_cls = globals()['Word'].__history_mapper__.class_

        part = Part.query.filter_by(id=self.part_id).first()
        word = word_history_cls.query.filter_by(id=self.word_id)\
            .filter_by(version=self.version).first()
        language = Language.query.filter(Language.id==word.language_id).first()
        
        markup = Markup(u'<a href="{0}">{1}</a> <em>under</em> {2}').format(
            url_for('words.view', word_data=word.word,
                    language_code=language.code), word.word, part.label)
        return markup

    def __repr__(self):
        return '<Word part of speech %r>' % self.word_id

class Relation(Versioned, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    part_id = db.Column(db.Integer, db.ForeignKey('part.id'),
                        unique=True)
    bidirectional = db.Column(db.Boolean)
    limit_ = db.Column(db.Integer)
    
    part = db.relationship("Part", lazy="joined")

    def __init__(self, part_id=None, bidirectional=None, limit=None):
        self.part_id = part_id
        self.bidirectional = bidirectional
        self.limit_ = limit

    @property
    def limit(self):
        return self.limit_ if not self.bidirectional else self.limit_*2

    @limit.setter
    def limit(self, value):
        self.limit_ = value

    def limit_reached(self, word_id):
        if not self.limit_:
            return False
        word_relations_count = WordRelation.query\
            .filter(WordRelation.relation_id==self.id)\
            .filter(or_(
                WordRelation.word_id_1==word_id, WordRelation.word_id_2==word_id
            )).count()
        
        relation_limit = self.limit_ if not self.bidirectional else self.limit_*2
        
        return not word_relations_count < relation_limit;

    @property
    def dependant_word_id(self):
        return None

    def __unicode__(self):
        part = Part.query.filter_by(id=self.part_id).first()
        markup = Markup(u'{0} <em>relationship</em>')
        return markup.format(part.label)
    
    def __repr__(self):
        return '<Relation %r>' % self.part_id

Part.relation = db.relationship("Relation", uselist=False)

class Translation(Versioned, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    word_id = db.Column(db.Integer, db.ForeignKey('word.id'))
    language_id = db.Column(db.Integer, db.ForeignKey('language.id'))
    part_id = db.Column(db.Integer, db.ForeignKey('part.id'),
                        default=None)
    
    language = db.relationship("Language", lazy="joined")
    word = db.relationship("Word")
    part = db.relationship("Part")
    
    def __init__(self, word_id=None, language_id=None, part_id=None):
        self.word_id = word_id
        self.language_id = language_id
        self.part_id = part_id

    @property
    def dependant_word_id(self):
        return self.word_id

    def __unicode__(self):
        word_history_cls = globals()['Word'].__history_mapper__.class_

        part = Part.query.filter_by(id=self.part_id).first()
        word = word_history_cls.query.filter(word_history_cls.id==self.word_id)\
            .filter(word_history_cls.version==self.version).first()
        language = Language.query.filter(Language.id==self.language_id).first()
        
        markup = Markup(u'Added {0} to <a href="{1}">{2}</a> for translations')
        markup = markup.format(language.label, url_for(
                'words.view', word_data=word.word, language_code=language.code),
                               word.word)
        return markup 


    def __repr__(self):
        return '<Transaltion %r>' % self.id

Definition.translation = db.relationship("Translation")


class WordRelation(Versioned, db.Model):
    """Relationships between words `plural, common noun, past tense, simile,
    direct translation, ...)` of a word (word_id_1).
    """
    id = db.Column(db.Integer, primary_key=True)
    word_id_1 = db.Column(db.Integer, db.ForeignKey('word.id'),
                          primary_key=True)
    word_id_2 = db.Column(db.Integer, db.ForeignKey('word.id'),
                          primary_key=True)
    relation_id = db.Column(db.Integer, db.ForeignKey('relation.id'),
                        primary_key=True)
    definition_id = db.Column(db.Integer, db.ForeignKey('definition.id'))
    translation_id = db.Column(db.Integer, db.ForeignKey('translation.id'),
                               default=None)
    
    word_1 = db.relationship("Word",
                             primaryjoin=Word.id==word_id_1,
                             lazy="joined")
    word_2 = db.relationship("Word",
                             primaryjoin=Word.id==word_id_2,
                             lazy="joined")
    relation = db.relationship("Relation", lazy="joined")
    translation = db.relationship("Translation", lazy="joined")

    def __init__(self, word_id_1=None, word_id_2=None, relation_id=None):
        self.word_id_1 = word_id_1
        self.word_id_2 = word_id_2
        self.relation_id = relation_id

    @property
    def dependant_word_id(self):
        """This is a bit tricky, both words can be considered "dependant words",
        but word_id_1 is the main word."""
        return self.word_id_1

    def __unicode__(self):
        word_history_cls = globals()['Word'].__history_mapper__.class_

        word_1 = word_history_cls.query.filter_by(id=self.word_id_1)
        word_2 = word_history_cls.query.filter_by(id=self.word_id_2)

        word_1 = word_1.filter(
            word_history_cls.created<self.created+datetime.timedelta(seconds=60)
        ).order_by('word_history.created DESC').first()
        language_1 = Language.query.filter_by(id=word_1.language_id).first()
        word_2 = word_2.filter(
            word_history_cls.created<self.created+datetime.timedelta(seconds=60)
        ).order_by('word_history.created DESC').first()
        language_2 = Language.query.filter_by(id=word_2.language_id).first()
        # I don't expect the part ID to change
        relation = Relation.query.filter_by(id=self.relation_id).first()

        markup = Markup(
            u'<a href="{0}">{1}</a> <em>{2} of</em> <a href="{3}">{4}</a>'
        )
        markup = markup.format(
            url_for('words.view', word_data=word_1.word, language_code=language_1.code),
            word_1.word, relation.part.label.lower(),
            url_for('words.view', word_data=word_2.word, language_code=language_2.code),
            word_2.word
        )
        return markup

    def __repr__(self):
        return '<Word relation %r:%r:%r>' % self.relation_id, \
            self.word_id_1, self.word_id_2


def zabalaza_pre_populate():
    """Insert fixtures to database"""
    from .fixtures.languages import data

    def add_part_row(data, parent_id=None, language_id=None):
        part = Part.query.filter_by(name =data['fields']['name'])\
            .filter_by(parent_id=parent_id)\
            .filter_by(language_id=language_id).first()
        if part is None:
            part = Part(
                name = data['fields']['name'],
                label = data['fields']['label'],
                parent_id = parent_id
            )
            part.language_id = language_id
        else:
            part.label = data['fields']['label']
            part.language_id = language_id
        db.session.add(part)
        db.session.commit()
        

        if 'relation' in data:
            relation = Relation.query.filter_by(part_id=part.id).first()
            if relation is None:
                relation = Relation(
                    part_id = part.id,
                    bidirectional = data['relation']['fields']['bidirectional'],
                    limit = data['relation']['fields']['limit'],
                )
            else:
                relation.bidirectional = data['relation']['fields']['bidirectional']
                relation.limit = data['relation']['fields']['limit']
            db.session.add(relation)
            db.session.commit()
                

        for i, row in enumerate(data['children']):
            add_part_row(row, parent_id=part.id, language_id=language_id)

    _languages = dict()
    for i, row in enumerate(data):
        language = Language.query.filter_by(name=row['fields']['name'])\
            .first()
        if language is None:
            language = Language(
                name = row['fields']['name'],
                label = row['fields']['label'],
                code = row['fields']['code'],
            )
        else:
            language.label = row['fields']['label']
        db.session.add(language)
        db.session.commit()
        _languages[language.code] = language.id

    for code, language_id in _languages.iteritems():
        try:
            _temp_import = __import__('fixtures.parts_{0}'.format(code),
                                      globals(), locals(), ['data'], -1)
            data = _temp_import.data
        except ImportError:
            continue
        
        for i, row in enumerate(data):
            add_part_row(row, language_id=language_id)
            
            
db.zabalaza_pre_populate = zabalaza_pre_populate

