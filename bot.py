# -*- coding: utf-8 -*-
import time
import telebot
import config
import dbworker
from telegram.ext import Updater, CommandHandler
import emoji
from googletrans import Translator
from googletrans import constants
from telebot import types
import unicodedata
import unidecode 
import re
import cherrypy
import urllib.request
import lang

WEBHOOK_HOST = 'ip'
WEBHOOK_PORT = 8443  # 443, 80, 88 или 8443 (порт должен быть открыт!)
WEBHOOK_LISTEN = '0.0.0.0'  # На некоторых серверах придется указывать такой же IP, что и выше

WEBHOOK_SSL_CERT = '/var/xalik/bot/cert.pem'  # Путь к сертификату
WEBHOOK_SSL_PRIV = '/var/xalik/bot/private.key'  # Путь к приватному ключу

WEBHOOK_URL_BASE = "https://%s:%s" % (WEBHOOK_HOST, WEBHOOK_PORT)
WEBHOOK_URL_PATH = "/%s/" % (config.token)

class WebhookServer(object):
    @cherrypy.expose
    def index(self):
        if 'content-length' in cherrypy.request.headers and \
                        'content-type' in cherrypy.request.headers and \
                        cherrypy.request.headers['content-type'] == 'application/json':
            length = int(cherrypy.request.headers['content-length'])
            json_string = cherrypy.request.body.read(length).decode("utf-8")
            update = telebot.types.Update.de_json(json_string)
            # Эта функция обеспечивает проверку входящего сообщения
            bot.process_new_updates([update])
            return ''
        else:
            raise cherrypy.HTTPError(403)

bot = telebot.TeleBot(config.token)


languages = constants.LANGUAGES
translator = Translator()
import logging
logging.basicConfig(filename='logs.log', level=logging.DEBUG, format=' %(asctime)s - %(levelname)s - %(message)s')

dest = ''
src = ''

def give_emoji_free_text(text):
    allchars = [str for str in text.decode('utf-8')]
    emoji_list = [c for c in allchars if c in emoji.UNICODE_EMOJI]
    clean_text = ' '.join([str for str in text.decode('utf-8').split() if not any(i in str for i in emoji_list)])
    return clean_text

OFFSET = 127462 - ord('A')

def convert(obj):
    try:
        return str(obj)
    except TypeError:
        return ''


def flag(code):
    code = code.upper()
    return chr(ord(code[0]) + OFFSET) + chr(ord(code[1]) + OFFSET)


"""for val in dbworker.all_users():
     try:
         bot.send_message(val, "test")
         logging.debug("test for id: " + str(val) + " done" + str(dbworker.all_users()))
         time.sleep(0.034)
     except Exception as e:
         logging.debug(e)"""
          
     
     

@bot.message_handler(commands=["start", "refresh"])
def entering_cmd(message):
     global src, dest
     dest = ''
     src = ''
     state = dbworker.get_current_state_sqlite(message.chat.id)
     markup = types.ReplyKeyboardMarkup(one_time_keyboard = True)
     markup.row('russian', 'english')
     markup.row('german', 'ukrainian')
     markup.row('auto')
     bot.send_message(message.chat.id, "С какого языка нужно перевести?", reply_markup=markup)
     dbworker.set_state_sqlite(message.chat.id, config.States.S_ENTER_SRC.value)

@bot.message_handler(func=lambda message: dbworker.get_current_state_sqlite(message.chat.id) == config.States.S_ENTER_SRC.value)
def entering_dest(message):
     global dest, src
     if message.text == 'russian' or message.text == 'english' or message.text == 'german' or message.text == 'ukrainian' or message.text == 'auto':
          src = lang.get_key(message.text)
          state = dbworker.get_current_state_sqlite(message.chat.id)
          markup = types.ReplyKeyboardMarkup(one_time_keyboard = True)
          markup.row('russian', 'english')
          markup.row('german', 'ukrainian')
          bot.send_message(message.chat.id, "На какой язык перевести?", reply_markup=markup)
          dbworker.set_state_sqlite(message.chat.id, config.States.S_ENTER_DEST.value)
     else:
          markup = types.ReplyKeyboardMarkup(one_time_keyboard = True)
          markup.row('russian', 'english')
          markup.row('german', 'ukrainian')
          bot.send_message(message.chat.id, "Используйте плиточки", reply_markup=markup)
          return
          
@bot.message_handler(func=lambda message: dbworker.get_current_state_sqlite(message.chat.id) == config.States.S_ENTER_DEST.value)
def trans(message):
     global dest, src
     if message.text == 'russian' or message.text == 'english' or message.text == 'german' or message.text == 'ukrainian':
          dest = lang.get_key(message.text)
          markup = types.ReplyKeyboardRemove()
          bot.send_message(message.chat.id, "Что перевести?", reply_markup=markup)
          dbworker.set_state_sqlite(message.chat.id, config.States.S_DOING.value)
     else:
          markup = types.ReplyKeyboardMarkup(one_time_keyboard = True)
          markup.row('russian', 'english')
          markup.row('german', 'ukrainian')
          bot.send_message(message.chat.id, "Используйте плиточки", reply_markup=markup)
          return
     

@bot.message_handler(func=lambda message: dbworker.get_current_state_sqlite(message.chat.id) == config.States.S_DOING.value)
def doing(message):
     global dest, src
     k = give_emoji_free_text(message.text.encode('utf8'))
     if message.text == 'russian' or message.text == 'english' or message.text == 'german' or message.text == 'ukrainian':
          return
     elif k != "" :
          try:
               if src != "auto":
                    bot.send_message(message.chat.id, translator.translate(k, dest=dest, src=src).text)
                    try:
                         logging.debug(message.text + " " + message.from_user.first_name + " " + message.from_user.last_name + " " + message.chat.id)
                    except Exception as e:
                         print(convert(e))

               else:
                    findedsrc = languages[translator.translate(k, dest=dest).src]
                    m = translator.translate(k, dest=dest).text
                    bot.send_message(message.chat.id, findedsrc + ": " + m)
                    try:
                         logging.debug(message.text + " " + message.from_user.first_name + " " + message.from_user.last_name + " " + message.chat.id)
                    except Exception as e:
                         print(convert(e))
               bot.send_message(message.chat.id, "Выбрать другие языки: /refresh")
          except:
               bot.send_message(message.chat.id, "Постарайтесь без смайликов, пожалуйста")
     else:
           bot.send_message(message.chat.id, "Не удалось перевести. Возможно вы отправили emoji")
           return

@bot.message_handler(content_types=["photo"])
def take_picture(message):
    global img_text
    bot.send_message(message.chat.id, "Секундочку...")
    fileID = message.photo[-1].file_id
    file_info = bot.get_file(fileID)
    m = file_info.file_path.replace('photos/', '')
    urllib.request.urlretrieve("https://api.telegram.org/file/bot" + config.token + "/"+file_info.file_path, m)
    import tess
    img_text = give_emoji_free_text(tess.whats_on_pic(m).encode('utf8'))
    markup = types.ReplyKeyboardMarkup(one_time_keyboard = True)
    markup.row('russian', 'english')
    markup.row('german', 'ukrainian')
    bot.send_message(message.chat.id, "На какой язык перевести?", reply_markup=markup)
    dbworker.set_state_sqlite(message.chat.id, config.States.S_DEST_IMG.value)

@bot.message_handler(func=lambda message: dbworker.get_current_state_sqlite(message.chat.id) == config.States.S_DEST_IMG.value)
def doing_img(message):
     global img_text
     if message.text == 'russian' or message.text == 'english' or message.text == 'german' or message.text == 'ukrainian':
          dest = lang.get_key(message.text)
          if (img_text != ""):
               findedsrc = languages[translator.translate(img_text, dest=dest).src]
               m = translator.translate(img_text, dest=dest).text
               bot.send_message(message.chat.id, findedsrc + ": " + m)
               bot.send_message(message.chat.id, "Выбрать другие языки: /refresh")
          else:
               bot.send_message(message.chat.id, "Не удалось распознать текст")
     else:
          markup = types.ReplyKeyboardMarkup(one_time_keyboard = True)
          markup.row('russian', 'english')
          markup.row('german', 'ukrainian')
          bot.send_message(message.chat.id, "Используйте плиточки", reply_markup=markup)
          return
     

bot.remove_webhook()
bot.set_webhook(url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH,
                certificate=open(WEBHOOK_SSL_CERT, 'r'))

cherrypy.config.update({
    'server.socket_host': WEBHOOK_LISTEN,
    'server.socket_port': WEBHOOK_PORT,
    'server.ssl_module': 'builtin',
    'server.ssl_certificate': WEBHOOK_SSL_CERT,
    'server.ssl_private_key': WEBHOOK_SSL_PRIV
})

cherrypy.quickstart(WebhookServer(), WEBHOOK_URL_PATH, {'/': {}})
