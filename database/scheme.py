from peewee import *

db = SqliteDatabase('./database/gateway.db')

class BaseModel(Model):
    class Meta:
        database = db

class Credential(BaseModel):
    apiID = CharField(unique=True)
    apiKey = CharField()

class Gateway(BaseModel):
    shortId = CharField(unique=True)
    name = CharField(null = True)
    lastSync = DateTimeField(null = True)
    hashKey = CharField(null = True)

class Node(BaseModel):
    shortId = CharField(unique=True)
    buildingName = CharField(null = True)
    lastOnline = DateTimeField(null = True)

class Card(BaseModel):
    cardId = CharField()
    cardStatus = CharField()
    pin = CharField()
    isTwoStepAuth = BooleanField()
    isBanned = BooleanField()

class AccessRole(BaseModel):
    card = ForeignKeyField(Card, backref="cards")
    node = ForeignKeyField(Node, backref="nodes")

