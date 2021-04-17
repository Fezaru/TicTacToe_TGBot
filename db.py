from peewee import *

db = SqliteDatabase('tictactoe_games.db')


class Game(Model):
    id = PrimaryKeyField()
    player_x = CharField()
    player_o = CharField()
    current_step = CharField()
    map = CharField()
    state = CharField()

    class Meta:
        database = db


db.create_tables([Game])
