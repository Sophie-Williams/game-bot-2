from peewee import PostgresqlDatabase
from peewee import Model
from peewee import BooleanField, IntegerField, ForeignKeyField, CharField


database = PostgresqlDatabase(
    database='docker', 
    user='docker', 
    password='docker', 
    host="localhost")


class BaseModel(Model):
    class Meta:
        database = database


class Lobby(BaseModel):
    chat = IntegerField()
    is_open = BooleanField(default=True)
    is_alive = BooleanField(default=True)


class LobbyMember(BaseModel):
    class Meta: 
        indexes = (
            (('user', 'lobby'), True),
        )
    user = IntegerField()
    username = CharField(null=True)
    lobby = ForeignKeyField(Lobby, backref='members')