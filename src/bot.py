import telebot
import time
import subprocess
import tabulate

import config
import netboxz
import memstat
import models


def auth(handler):
    def wrapper_handler(message):
        print("Message from ", message.chat.id)
        try:
            chat = models.Chat.select().where(models.Chat.id == message.chat.id).get()
        except models.Chat.DoesNotExist:
            return

        handler(message, chat.user)

    return wrapper_handler

bot = telebot.TeleBot(config.token)

@bot.message_handler(commands=["job_status"])
@auth
def get_job_status(message, user):
    pass

@bot.message_handler(commands=["temp"])
@auth
def get_temp(message, user):
    data = [
            ['Front 1', netboxz.temp(1)],
            ['Front 2', netboxz.temp(2)],
            ['Back'   , netboxz.temp(3)],
    ]
    table = tabulate.tabulate(data, headers=['Loc', 'Temp (C)'])
    bot.send_message(message.chat.id, '<pre>{}</pre>'.format(table), parse_mode='HTML')

@bot.message_handler(commands=["login"])
def login(message):
    try:
        chat = models.Chat.select().where(models.Chat.id == message.chat.id).get()
        bot.send_message(message.chat.id, "Already logged in")
    except models.Chat.DoesNotExist:
        args = message.text.split()
        if len(args) == 2:
            token = args[1]
            try:
                user = models.User.select().where(models.User.token == token).get()
            except models.User.DoesNotExist:
                bot.send_message(message.chat.id, "Login failed")
                return

            models.Chat.create(user=user, id=message.chat.id)
            bot.send_message(message.chat.id, "Login successful")
        else:
            bot.send_message(message.chat.id, "Login failed")

@bot.message_handler(commands=["squeue"])
@auth
def get_queue(message, user):
    res = subprocess.run(['squeue', '-o', '%.5i %.9P %.8j %.8u %.2t %.10M %.1D'], stdout=subprocess.PIPE)
    bot.send_message(message.chat.id, "<pre>{}</pre>".format(res.stdout.decode('utf-8')), parse_mode="HTML")

@bot.message_handler(commands=["memstat"])
@auth
def get_memstat(message, user):
    memdata = memstat.format_memdata(config.node_list)
    bot.send_message(message.chat.id, "<pre>{}</pre>".format(memdata), parse_mode="HTML")

if __name__ == '__main__':
    while True:
        try:
            bot.polling(none_stop=True, interval=5, timeout=20)
        except Exception as err:
            print(err)
            time.sleep(30)
