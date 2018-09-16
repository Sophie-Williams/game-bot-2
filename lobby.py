# coding: utf-8
from peewee import IntegrityError
from telegram import Bot, Update
import numpy as np
from random import shuffle
from collections import deque

from models import database
from models import Lobby, LobbyMember, Player
import utils

MONSTER_NAMES = ['Гигазавр', 'Кибер Киса', 'Космо Пингвин', 'Кинг']
LOBBY_NOT_CREATED_MESSAGE = "Для начала создайте комнату, нажмите /create_lobby."


@database.atomic()
def create_lobby(bot: Bot, update: Update):
    if utils.lobby_is_alive(update):
        return update.effective_message.reply_text(
            "В этом чате уже создана комната, где все еще идет игра. Дождитесь, "
            "пока эта игра завершится, либо создайте новую /force_create_lobby.", quote=False)
    else:
        db_create_lobby(update,
                        "Комната создана. Чтобы присоединиться, нажмите /join_lobby.")


@database.atomic()
def force_create_lobby(bot: Bot, update: Update):
    utils.lobby_lock(update.effective_chat.id)
    update.effective_message.reply_text(
        "Предыдущая игра остановлена, комната закрыта.", quote=False)

    db_create_lobby(update,
                    "Создана новая комната. Чтобы присоединиться, нажмите /join_lobby.")


@database.atomic()
def join_lobby(bot: Bot, update: Update):
    try:
        lobby = utils.get_current_lobby(update)
        if not lobby.is_open:
            return update.effective_message.reply_text(
                "Больше в текущую комнату присоединиться нельзя.")

        LobbyMember.create(
            user=update.effective_user.id,
            username=update.effective_user.username,
            lobby=lobby.id)
        update.effective_message.reply_text(
            f"@{update.effective_user.username} вошел в комнату.", quote=False)

    except IntegrityError:
        update.effective_message.reply_text("Вы уже вошли в эту комнату.")
    except ValueError:
        return update.effective_message.reply_text(LOBBY_NOT_CREATED_MESSAGE)


@database.atomic()
def leave_lobby(bot: Bot, update: Update):
    try:
        current_member = LobbyMember.select().where(
            (LobbyMember.user == update.effective_user.id) &
            (LobbyMember.lobby == utils.get_current_lobby(update).id)).first()
    except ValueError:
        return update.effective_message.reply_text(LOBBY_NOT_CREATED_MESSAGE)
    if current_member:
        current_member.delete_instance()
        update.effective_message.reply_text(
            f"@{update.effective_user.username} покинул комнату", quote=False)


@database.atomic()
def members_lobby(bot: Bot, update: Update):
    try:
        message = "Сейчас в игровой комнате находятся: \n\n"
        lobby = utils.get_current_lobby(update)
        if lobby.is_open:
            for member in lobby.members:
                message = f"{message}{'@' + member.username if member.username else 'кто-то'}\n"
        else:
            for player in lobby.players:
                message = f"{message}{player.name} (@{player.lobby_member.username})\n"
        update.effective_message.reply_text(message, quote=False)
    except ValueError:
        return update.effective_message.reply_text(LOBBY_NOT_CREATED_MESSAGE)


@database.atomic()
def start_game(bot: Bot, update: Update, chat_data: dict):
    try:
        lobby = utils.get_current_lobby(update)
    except ValueError:
        return update.effective_message.reply_text(LOBBY_NOT_CREATED_MESSAGE)

    if lobby.author != update.effective_user.id:
        return update.effective_message.reply_text(
            f"Вы не можете начать игру, это может сделать только создатель комнаты (@{lobby.author_username}).")

    if len(lobby.members) > len(MONSTER_NAMES):
        return update.effective_message.reply_text(
            f"Превышен максимум ({len(MONSTER_NAMES)}) игроков в комнате.")

    names = np.random.choice(MONSTER_NAMES, size=len(MONSTER_NAMES), replace=False).tolist()
    for member in lobby.members:
        Player.create(lobby=lobby.id, lobby_member=member.id, name=names.pop())

    lobby.is_open = False
    lobby.save()

    chat_data["rolled_dices"] = False
    chat_data["rewarded"] = False
    chat_data["shopped"] = False
    chat_data["left_dice_rolls"] = 3
    chat_data["num_dices"] = 6

    # define queue
    ids = [member.id for member in lobby.members]
    shuffle(ids)
    chat_data["queue"] = deque([item.id for item in Player.select().where(Player.lobby_member.in_(ids))])
    utils.update_player_queue(chat_data)

    update.effective_message.reply_text("Игра началась!", quote=False)


def init(bot: Bot, update: Update, chat_data: dict):
    players = list(Player.select().order_by(Player.id.desc()))
    player = players[0]
    chat_data.update({
        "current_player_id": player.id,
        "current_player_username": player.lobby_member.username,
        "current_player_nickname": player.name,
        "rolled_dices": False,
        "rewarded": False,
        "shopped": False,
        "left_dice_rolls": 3,
        "num_dices": 6,
        "queue": [it.id for it in players]
    })
    update.effective_message.reply_text("Данные инициированы")


def db_create_lobby(update: Update, reply_text: str, quote=False):
    utils.lobby_create(chat_id=update.effective_chat.id,
                       author_id=update.effective_user.id,
                       author_username=update.effective_user.username)
    update.effective_message.reply_text(reply_text, quote=quote)
