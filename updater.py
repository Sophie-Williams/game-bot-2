# coding: utf-8
import logging
from decouple import Config, RepositoryEnv
from telegram.ext import Updater
from telegram.ext import CommandHandler
from telegram import Bot, Update

import models
import lobby
from models import database


config = Config(RepositoryEnv('config.env'))
updater = Updater(token=config('TOKEN'))
dispatcher = updater.dispatcher

logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def start(bot: Bot, update: Update):
    update.effective_message.reply_text(
        'Добро пожаловать в царство "Властелина Казани". Это карточная игра, предназначенная '
        'для небольшой компании, в которой каждый найдет толику забавы и не останется разочарован. '
        'Игра находится на стадии разработки. Чтобы начать игру, нажмите /create_lobby.',
        quote=False)


def help(bot: Bot, update: Update):
    update.effective_message.reply_text(
        "/create_lobby - создать комнату\n"
        "/force_create_lobby - закрыть старую комнату и создать новую\n"
        "/join_lobby - присоединиться к комнате\n"
        "/leave_lobby - выйти из комнаты\n" 
        "/members_lobby - список участников",
        quote=False
    )


def error(bot: Bot, update: Update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)


# default commands
dispatcher.add_error_handler(error)
dispatcher.add_handler(CommandHandler('start', start))
dispatcher.add_handler(CommandHandler('help', help))
dispatcher.add_handler(CommandHandler('create_lobby', lobby.create_lobby))
dispatcher.add_handler(CommandHandler('force_create_lobby', lobby.force_create_lobby))
dispatcher.add_handler(CommandHandler('join_lobby', lobby.join_lobby))
dispatcher.add_handler(CommandHandler('leave_lobby', lobby.leave_lobby))
dispatcher.add_handler(CommandHandler('members_lobby', lobby.members_lobby))
dispatcher.add_handler(CommandHandler('start_game', lobby.start_game))


if __name__ == '__main__':
    database.create_tables([models.Lobby, models.LobbyMember, models.Player, models.Card, models.PlayerCards])
    updater.start_polling()
    updater.idle()