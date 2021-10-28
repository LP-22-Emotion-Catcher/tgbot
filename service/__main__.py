import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from flask import Flask
import httpx

from service.config import TOKEN

app = Flask(__name__)

logging.basicConfig(format='%(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO,
                    filename='bot.log')


PROXY = {
    'proxy_url': 'socks5://t1.learn.python.ru:1080',
    'urllib3_proxy_kwargs': {
        'username': 'learn',
        'password': 'python'
    }
}


def greet_user(update, context):
    text = 'Привет ! Я умею распознавать эмоциональный окрас текстов !\nДля этого отправь мне текст в формате:\n/predict твой текст'
    print(text)
    update.message.reply_text(text)


def default_response_to_user(update, context):
    user_text = update.message.text
    text = f'Для распознавания эмоциональной окраски текста отправь мне текст в формате:\n/predict твой текст'
    update.message.reply_text(text)


@app.route("/api/v1/emotions", methods=['POST'])
def get_emotions(update, context):
    text = update.message.text
    text = text.replace('/predict ', '')
    logging.info(text)
    payload = {'text': text}
    emotion = httpx.post('http://127.0.0.1:5000/api/v1/predict', json=payload)
    emotion = emotion.json()['emotions'][0]
    update.message.reply_text('''Определение эмоциональной окраски комментария:\n"{}"\n
                                РАСПОЗНАНО, КАК: {}'''.format(text, emotion))


@app.route("/api/v1/posts", methods=['GET'])
def get_posts(update, context):
    text = update.message.text
    text = text.replace('/posts ', '')
    uid = text.split()[0]
    need_emotion = text.split()[1]
    logging.info(text)
    posts = httpx.get(f'http://127.0.0.1:5001/api/v1/walls/{uid}/posts/?emotion={{{need_emotion}}}')
    update.message.reply_text('''Указанной эмоциональной окраске: {} \nCоответствуют комментарии:\n"{}"\n'''
                              .format(need_emotion, posts.json()[0]['text']))


@app.route("/api/v1/wall", methods=['POST'])
def set_wall(update, context):
    text = update.message.text[1]
    print(text)
    data = text.split('-')
    wall = "-" + str(data[1])
    logging.info(wall)
    update.message.reply_text(wall)
    payload = {
        "wall": wall,
        "link": text,
        "uid": "-1"
    }
    update.message.reply_text(payload)
    try:
        httpx.post('http://localhost:5001/api/v1/walls', json=payload)
        update.message.reply_text('Ваша стена добавлена в базу')
    except httpx.ConnectError:
        logging.info("Can\'t connect to backend")


def main():
    mybot = Updater(TOKEN, use_context=True)
    dp = mybot.dispatcher
    dp.add_handler(CommandHandler("setwall", set_wall))
    dp.add_handler(CommandHandler("predict", get_emotions))
    dp.add_handler(CommandHandler("posts", get_posts))
    dp.add_handler(CommandHandler("start", greet_user))
    dp.add_handler(MessageHandler(Filters.text, default_response_to_user))
    mybot.start_polling()
    mybot.idle()
    logging.basicConfig(level=logging.INFO)
    app.run(port=5005, debug=True)


if __name__ == "__main__":
    main()
