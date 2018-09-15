import numpy as np 
from telegram import Update
from models import database
from models import Lobby, GameState, LobbyMember, Player


def roll(previous=None, positions=None, num_dices=6) -> np.array:
    if previous is None: previous = np.zeros(num_dices)
    if positions is None: 
        previous = np.random.random_integers(1, 6, num_dices)
    else:
        previous[positions,] = np.random.random_integers(1, 6, len(positions))
    return previous


@database.atomic()
def get_current_lobby(update):
    """ Return current active lobby """
    lobby = Lobby.select().where(
        (Lobby.chat == update.effective_chat.id) & 
        (Lobby.is_alive)).order_by(Lobby.id.desc()).first()
    
    if not lobby: raise ValueError("Lobby cannot be found")
    return lobby


@database.atomic()
def get_last_move(lobby: Lobby) -> Lobby:
    return GameState.select().where(
        GameState.lobby == lobby).order_by(GameState.id.desc()).first()


@database.atomic()
def get_current_player(lobby: Lobby, update: Update) -> Player:
    return LobbyMember.select().where(
        (LobbyMember.user == update.effective_user.id) & 
        (LobbyMember.id.in_(lobby.members))
        ).first().player.first()


@database.atomic()
def get_current_player_by_id(_id: int):
    return Player.get_by_id(_id)


@database.atomic()
def update_player_queue(chat_data: dict):
    queue = chat_data["queue"]
    previous_player_id = queue.popleft()
    queue.append(previous_player_id)
    
    current_player_id = queue.popleft()
    queue.appendleft(current_player_id)
    
    player = Player.get_by_id(current_player_id)
    chat_data["current_player_id"] = current_player_id
    chat_data["current_player_username"] = player.lobby_member.username
    chat_data["current_player_nickname"] = player.name
    chat_data["queue"] = queue