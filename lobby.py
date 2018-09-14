# coding: utf-8
from peewee import IntegrityError
from telegram import Bot, Update
import random

from models import database
from models import Lobby, LobbyMember, Player

MONSTER_NAMES = ['Гигазавр', 'Кибер Киса', 'Космо Пингвин', 'Кинг']
LOBBY_NOT_CREATED_MESSAGE = "Для начала создайте комнату, нажмите /create_lobby."


def _get_current_lobby(update):
    """ Return current active lobby """
    lobby = Lobby.select().where(
        (Lobby.chat == update.effective_chat.id) & 
        (Lobby.is_alive)).order_by(Lobby.id.desc()).first()
    
    if not lobby: raise ValueError("Lobby cannot be found")
    return lobby


@database.atomic()
def create_lobby(bot: Bot, update: Update):
    if Lobby.select().where((Lobby.chat == update.effective_chat.id) & (Lobby.is_alive)).first():
        return update.effective_message.reply_text(
            "В этом чате уже создана комната, где все еще идет игра. Дождитесь, "
            "пока эта игра завершится, либо создайте новую /force_create_lobby.")
    Lobby.create(
        chat=update.effective_chat.id, 
        author=update.effective_user.id,
        author_username=update.effective_user.username)
    update.effective_message.reply_text(
        "Комната создана. Чтобы присоединиться, нажмите /join_lobby.")


@database.atomic()
def force_create_lobby(bot: Bot, update: Update):
    Lobby.update({"is_alive": False}).where(
        (Lobby.chat == update.effective_chat.id) & 
        (Lobby.is_alive)).execute()
    update.effective_message.reply_text(
        "Предыдущая игра остановлена, комната закрыта.")
    
    Lobby.create(
        chat=update.effective_chat.id, 
        author=update.effective_user.id,
        author_username=update.effective_user.username)
    update.effective_message.reply_text(
        "Создана новая комната. Чтобы присоединиться, нажмите /join_lobby.")


@database.atomic()
def join_lobby(bot: Bot, update: Update):
    try: 
        lobby = _get_current_lobby(update)
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
            (LobbyMember.lobby == _get_current_lobby(update).id)).first()
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
        lobby = _get_current_lobby(update)
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
def start_game(bot: Bot, update: Update):
    try: 
        lobby = _get_current_lobby(update)
        if lobby.author != update.effective_user.id:
            return update.effective_message.reply_text(
                f"Вы не можете начать игру, это может сделать только создатель комнаты (@{lobby.author_username}).")
        
        if len(lobby.members) > len(MONSTER_NAMES): 
            return update.effective_message.reply_text(
                f"Превышен максимум ({len(MONSTER_NAMES)}) игроков в комнате.")

        names = random.sample(MONSTER_NAMES, len(MONSTER_NAMES))
        for member in lobby.members:
            Player.create(lobby=lobby.id, lobby_member=member.id, name=names.pop())

        lobby.is_open = False
        lobby.save()
        update.effective_message.reply_text("Игра началась!", quote=False)
    except ValueError:
        return update.effective_message.reply_text(LOBBY_NOT_CREATED_MESSAGE)
    