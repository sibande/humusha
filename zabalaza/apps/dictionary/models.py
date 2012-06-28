
import datetime
from sqlalchemy import or_
from sqlalchemy.orm import aliased, joinedload, mapper
from flask import session

from zabalaza import db

from zabalaza.utils.history_meta import Versioned, versioned_session



class Language(Versioned, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(1000))
    label = db.Column(db.String(1000))
    code = db.Column(db.String(20))
    
    def __init__(self, name, label, code):
        self.name = name
        self.code = code
        self.label = label

    def __repr__(self):
        return '<Language %r (%r)>' % self.name, self.code


class Word(Versioned, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(1000))
    language_id = db.Column(db.Integer, db.ForeignKey('language.id'))

    def __init__(self, word, language_id):
        self.word = word
        self.language_id = language_id

    def definitions(self, part_id):
        return Definition.query.filter(Definition.part_id==part_id)\
            .filter(Definition.word_id==self.id)

    def relations(self, part_id, definition_id=None):
        relation = Relation.query.filter(Relation.part_id==part_id).first()
        if relation is None:
            return []
        word_relations = WordRelation.query.filter(
            or_(WordRelation.word_id_1==self.id, WordRelation.word_id_2==self.id)
        ).filter(WordRelation.relation_id==relation.id)\
        .filter(WordRelation.definition_id==definition_id)
        return word_relations
        
    def __repr__(self):
        return '<Word %r>' % self.word


class Part(Versioned, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(1000))
    label = db.Column(db.String(1000))
    parent_id = db.Column(db.Integer, db.ForeignKey('part.id'))
    language_id = db.Column(db.Integer, db.ForeignKey('language.id'))

    parent = db.relationship("Part", remote_side=[id])
    
    def __init__(self, name, label, parent_id):
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

    def __repr__(self):
        return '<Part of speech %r>' % self.label


class Definition(Versioned, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    definition = db.Column(db.Text)
    word_id = db.Column(db.Integer, db.ForeignKey('word.id'))
    part_id = db.Column(db.Integer, db.ForeignKey('part.id'))
    
    word = db.relationship("Word")
    part = db.relationship("Part")

    def __init__(self, definition, word_id, part_id):
        self.definition = definition
        self.word_id = word_id
        self.part_id = part_id
        
    def __repr__(self):
        return '<Definition %r>' % self.definition


class Etymology(Versioned, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    word_id = db.Column(db.Integer, db.ForeignKey('word.id'))
    etymology = db.Column(db.Text)
    
    def __init__(self, word_id, etymology):
        self.word_id = word_id
        self.etymology = etymology
        
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
    
    def __init__(self, row_id, word_id, version, model, action):
        self.row_id = row_id
        self.word_id = word_id
        self.version = version
        self.model = model
        self.action = action
        
    def __repr__(self):
        return '<Change %r>' % self.word_id



class Usage(Versioned, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    definition_id = db.Column(db.Integer, db.ForeignKey('definition.id'))
    sentence = db.Column(db.Text)
    
    definition = db.relationship("Definition")
    
    def __init__(self, sentence, definition_id):
        self.sentence = sentence
        self.definition_id = definition_id
        
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

    def __init__(self, word_id, part_id):
        self.word_id = word_id
        self.part_id = part_id

    @property
    def part_types(self):
        return self.query.join(Part).filter(Part.parent_id==self.part_id)\
            .filter('word_part.word_id={0}'.format(self.word_id))

    def __repr__(self):
        return '<Word part of speech %r>' % self.word_id

class Relation(Versioned, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    part_id = db.Column(db.Integer, db.ForeignKey('part.id'),
                        unique=True)
    bidirectional = db.Column(db.Boolean)
    limit_ = db.Column(db.Integer)
    
    part = db.relationship("Part", lazy="joined")

    def __init__(self, part_id, bidirectional, limit):
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
    
    def __repr__(self):
        return '<Relation %r>' % self.part_id

Part.relation = db.relationship("Relation", uselist=False)


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

    word_1 = db.relationship("Word",
                             primaryjoin=Word.id==word_id_1,
                             lazy="joined")
    word_2 = db.relationship("Word",
                             primaryjoin=Word.id==word_id_2,
                             lazy="joined")
    relation = db.relationship("Relation", lazy="joined")

    def __init__(self, word_id_1, word_id_2, relation_id):
        self.word_id_1 = word_id_1
        self.word_id_2 = word_id_2
        self.relation_id = relation_id

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
        print '.fixtures.parts_{0}'.format(code)
        try:
            _temp_import = __import__('fixtures.parts_{0}'.format(code),
                                      globals(), locals(), ['data'], -1)
            data = _temp_import.data
        except ImportError:
            continue
        
        for i, row in enumerate(data):
            add_part_row(row, language_id=language_id)
            
            
db.zabalaza_pre_populate = zabalaza_pre_populate

