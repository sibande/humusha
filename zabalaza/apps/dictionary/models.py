import datetime

from zabalaza import db


class Word(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(1000))
    created = db.Column(db.DateTime(timezone=True), default=datetime.datetime.now)

    def __init__(self, word):
        self.word = word


    def definitions(self, part_id):
        return Definition.query.filter(Definition.part_id==part_id)
        
    def __repr__(self):
        return '<Word %r>' % self.word
    

class Part(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(1000))
    label = db.Column(db.String(1000))
    parent_id = db.Column(db.Integer, db.ForeignKey('part.id'))
    # value_type_id = db.Column(db.Integer, db.ForeignKey('value_type.id'))

    def __init__(self, name, parent_id):
        self.name = name
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


# class ValueType(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(1000))
#     label = db.Column(db.String(1000))
    
#     def __init__(self, name, parent):
#         self.label = label
        
#     def __repr__(self):
#         return '<Value type %r>' % self.label


class WordPart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    word_id = db.Column(db.Integer, db.ForeignKey('word.id'), primary_key=True)
    part_id = db.Column(db.Integer, db.ForeignKey('part.id'), primary_key=True)
    
    word = db.relationship("Word", lazy="joined")
    part = db.relationship("Part", lazy="joined")

    def __init__(self, word_id, part_id):
        self.word_id = word_id
        self.part_id = part_id

    def __repr__(self):
        return '<Word part of speech %r>' % self.word_id

    
