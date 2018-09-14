# coding: utf-8
import numpy as np
from telegram import Bot, Update

from models import Lobby, Player, PlayerCards, Card, GameState, LobbyMember
from lobby import _get_current_lobby

MOVE_ENTER, MOVE_ROLL = range(2)


def _get_last_move(lobby: Lobby) -> Lobby:
    return GameState.select().where(GameState.lobby == lobby).order_by(GameState.id.desc()).first()


def _get_current_player(lobby: Lobby, update: Update) -> Player:
    return LobbyMember.select().where(
        (LobbyMember.user == update.effective_user.id) & 
        (LobbyMember.id.in_(lobby.members))
        ).first().player.first()


def _roll(previous=None, positions=None, num_dices=6) -> np.array:
    if previous is None: previous = np.zeros(num_dices)
    if positions: 
        previous[positions,] = np.random.random_integers(1, 6, len(positions))
    else:
        previous = np.random.random_integers(1, 6, num_dices)
    return previous


def roll(bot: Bot, update: Update, args):
    try: 
        args = list(map(int, args))
        if len(args) > 6: raise ValueError
    except ValueError:
        return update.effective_message.reply_text("Нахуй пошел, умник блять.")
    
    try:
        lobby = _get_current_lobby(update)
        move = _get_last_move(lobby)
        player = _get_current_player(lobby, update)
        dices = _roll().tolist()
        GameState.create(lobby=lobby.id, player=player.id, move_type='roll', 
            dices=','.join(map(str, dices)),roll_dice_number=1)
        update.effective_message.reply_text(
            f"{player.name} (@{player.lobby_member.username}) выбросил {dices}", quote=False)
    except ValueError:
        update.effective_message.reply_text("Игра еще не начата.", quote=False)