# coding: utf-8
import numpy as np
from telegram import Bot, Update

from models import Lobby, Player, PlayerCards, Card, GameState, LobbyMember
import utils

ROLL, MOVE_ROLL = range(2)


def roll(bot: Bot, update: Update, args: list, chat_data: dict):
    try:
        lobby = utils.get_current_lobby(update)
        player = utils.get_current_player_by_id(chat_data["current_player_id"])
    except ValueError:
        return update.effective_message.reply_text("Игра еще не начата.", quote=False)
    except KeyError:
        lobby.is_open = False
        lobby.is_alive = False
        lobby.save()
        return update.effective_message.reply_text(
            "Сервер был перезапущен, предыдущая игра была закрыта. Создайте новую комнату /create_lobby", 
            quote=False)

    try: 
        args = (np.array(list(map(int, args))) - 1) if args else None
    except ValueError:
        phrases, weights = [
            "Неправильные аргументы. Введите цифры, например, /roll 1 2 4", 
            "Нахуй пошел, умник блятб"], [0.95, 0.05]
        return update.effective_message.reply_text(np.random.choice(phrases, p=weights))

    if player.lobby_member.user != update.effective_user.id:
        return update.effective_message.reply_text(
            f"Сейчас ход не ваш. Ходит @{chat_data['current_player_username']}", quote=False)
    if chat_data["left_dice_rolls"] == 0:
        chat_data["left_dice_rolls"] = 3
        utils.update_player_queue(chat_data)
        return update.effective_message.reply_text(
            f"Больше не осталось бросков. Следующим ходит @{chat_data['current_player_username']}")
        # return update.effective_message.reply_text(f"Больше не осталось бросков. Разыграйте результат /draw")

    last_move = GameState.select().where(
        (GameState.lobby == lobby.id) & 
        (GameState.player == player.id) & 
        (GameState.move_type == 'roll')
    ).order_by(GameState.id.desc()).first()

    previous = np.array(list(map(int, last_move.dices.split(',')))) if args is not None else None
    dices = utils.roll(previous=previous, positions=args).tolist()
    GameState.create(lobby=lobby.id, player=player.id, move_type='roll', 
        dices=','.join(map(str, dices)))
    update.effective_message.reply_text(
        f"{player.name} (@{player.lobby_member.username}) выбросил {dices}", quote=False)

    chat_data["left_dice_rolls"] -= 1
    chat_data["rolled_dices"] = True


def draw(bot: Bot, update: Update, chat_data: dict):
    pass


def shop(bot: Bot, update: Update, chat_data: dict):
    pass