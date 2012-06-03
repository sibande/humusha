import datetime

from zabalaza import db


class Word(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(1000))
    created = db.Column(db.DateTime(timezone=True), default=datetime.datetime.now)

    def __init__(self, word):
        self.word = word


    def definitions(self, part_id):
        return Definition.query.filter(Definition.part_id==part_id)\
            .filter(Definition.word_id==self.id)
        
    def __repr__(self):
        return '<Word %r>' % self.word
    

class Part(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(1000))
    label = db.Column(db.String(1000))
    parent_id = db.Column(db.Integer, db.ForeignKey('part.id'))

    def __init__(self, name, label, parent_id):
        self.name = name
        self.label = label
        self.parent_id = parent_id
        
    def __repr__(self):
        return '<Part of speech %r>' % self.label


class Definition(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    definition = db.Column(db.Text)
    word_id = db.Column(db.Integer, db.ForeignKey('word.id'))
    part_id = db.Column(db.Integer, db.ForeignKey('part.id'))
    
    usage_examples = db.relationship('Usage')
    word = db.relationship("Word")
    part = db.relationship("Part")

    
    def __init__(self, definition, word_id, part_id):
        self.definition = definition
        self.word_id = word_id
        self.part_id = part_id
        
    def __repr__(self):
        return '<Definition %r>' % self.definition


class Usage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    definition_id = db.Column(db.Integer, db.ForeignKey('definition.id'))
    sentence = db.Column(db.Text)
    
    definition = db.relationship("Definition")
    
    def __init__(self, sentence, definition_id):
        self.sentence = sentence
        self.definition_id = definition_id
        
        
    def __repr__(self):
        return '<Sentence %r>' % self.definition_id


class WordPart(db.Model):
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

class Relation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    part_id = db.Column(db.Integer, db.ForeignKey('part.id'),
                        unique=True)
    bidirectional = db.Column(db.Boolean)
    limit = db.Column(db.Integer)
    
    part = db.relationship("Part", lazy="joined")

    def __init__(self, part_id, bidirectional, limit):
        self.part_id = part_id
        self.bidirectional = bidirectional
        self.limit = limit
    
    def __repr__(self):
        return '<Relation %r>' % self.part_id



class WordRelation(db.Model):
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
    from fixtures import data
    
    def add_row(data, parent_id = None):
        part = Part.query.filter_by(name =data['fields']['name'])\
            .filter_by(parent_id=parent_id).first()
        if part is None:
            part = Part(
                name = data['fields']['name'],
                label = data['fields']['label'],
                parent_id = parent_id,
            )
        else:
            part.label = data['fields']['label']

        db.session.add(part)
        db.session.commit()

        for i, row in enumerate(data['children']):
            add_row(row, parent_id = part.id)

    for i, row in enumerate(data):
        add_row(row)
            
db.zabalaza_pre_populate = zabalaza_pre_populate

