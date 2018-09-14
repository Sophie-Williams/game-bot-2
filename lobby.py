from peewee import IntegrityError
from telegram import Bot, Update

from models import database
from models import Lobby, LobbyMember

LOBBY_NOT_CREATED_MESSAGE = "Для начала создайте комнату.\n/create_lobby"


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
    Lobby.create(chat=update.effective_chat.id)
    update.effective_message.reply_text(
        "Комната создана. Чтобы присоединиться, нажмите /join_lobby.")


@database.atomic()
def force_create_lobby(bot: Bot, update: Update):
    Lobby.update({"is_alive": False}).where(
        (Lobby.chat == update.effective_chat.id) & 
        (Lobby.is_alive)).execute()
    update.effective_message.reply_text(
        "Предыдущая игра остановлена, комната закрыта.")
    
    Lobby.create(chat=update.effective_chat.id)
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
        update.effective_message.reply_text(LOBBY_NOT_CREATED_MESSAGE)


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
        for member in LobbyMember.select().where(LobbyMember.lobby == _get_current_lobby(update).id):
            message = f"{message}{'@' + member.username if member.username else 'кто-то'}\n"
        update.effective_message.reply_text(message, quote=False)
    except ValueError:
        update.effective_message.reply_text(LOBBY_NOT_CREATED_MESSAGE)