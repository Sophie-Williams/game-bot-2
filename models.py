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
    author = IntegerField()
    author_username = CharField(null=True)
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


class Player(BaseModel):
    lobby = ForeignKeyField(Lobby, backref='players')
    lobby_member = ForeignKeyField(LobbyMember, backref='player')
    name = CharField()
    health = IntegerField(default=10)
    stars = IntegerField(default=0)
    energy = IntegerField(default=0)


class Card(BaseModel):
    name = CharField()
    definition = CharField()
    energy_cost = IntegerField()


class PlayerCards(BaseModel):
    player = ForeignKeyField(Player, backref='cards')
    active_cards = ForeignKeyField(Card, backref='cards')


class GameState(BaseModel):
    lobby = ForeignKeyField(Lobby, backref='game')
    player = ForeignKeyField(Player, backref='moves')

    move_type = CharField() # roll, reward, buy, die
    dices = CharField()

    # It this the start or the end of the players move
    is_start = BooleanField(default=False)
    is_end = BooleanField(default=False)

