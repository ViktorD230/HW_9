from mongoengine import Document
from mongoengine.fields import ListField, StringField, ReferenceField

class Authors(Document):
    fullname = StringField()
    born_date = StringField()
    born_location = StringField()
    description = StringField()
    meta = {'allow_inheritance': True}

class Quotes(Document):
    tags = ListField(StringField())
    author = ReferenceField(Authors)
    quote = StringField()
    meta = {'allow_inheritance': True}


   