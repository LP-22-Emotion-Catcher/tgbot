import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import httpx
import re

from service.config import TOKEN, emotion_url, backend_url


# logging.basicConfig(format='%(name)s - %(levelname)s - %(message)s',
#                    level=logging.INFO,
#                    filename='bot.log')
logger = logging.getLogger(__name__)

PROXY = {
    'proxy_url': 'socks5://t1.learn.python.ru:1080',
    'urllib3_proxy_kwargs': {
        'username': 'learn',
        'password': 'python'
    }
}


def greet_user(update, context):
    text = """Привет! Я умею распознавать эмоциональный окрас текстов! Для получения полного\
 списка доступных команд введите /help"""
    update.message.reply_text(text)


def default_response_to_user(update, context):
    # user_text = update.message.text
    text = """Для распознавания эмоциональной окраски текста отправь мне текст\
 в формате: /predict твой текст либо /help для доступа к командам"""
    update.message.reply_text(text)


def print_help(update, context):
    text = """Команды:\n
 /predict твой текст - определяет эмоциональный окрас текста\n
 Пример: /predict Какой замечательный сегодня день!\n
 /set_wall ссылка на стену в контакте - добавляет стену в базу\n
 Пример: /set_wall https://vk.com/wall-101982925\n
 /posts номер стены эм.окраска - возвращает пост со стены с эм.окраской\n
 Пример: /posts -101982925 positive (доступные варианты: negative, neutral, skip, speech)"""
    update.message.reply_text(text)


def get_emotions(update, context):
    text = update.message.text
    text = text.replace('/predict ', '')
    logging.info(f'This is your text: {text}')
    payload = {'text': text}
    try:
        emotion = httpx.post(f'{emotion_url}/api/v1/predict', json=payload)
    except httpx.ConnectError:
        logging.info('Can\'t connect with emotion service. No emotion color is received')

    emotion = emotion.json()['emotions'][0]
    update.message.reply_text('''Определение эмоциональной окраски комментария:\n"{}"\n
                                РАСПОЗНАНО, КАК: {}'''.format(text, emotion))


def get_posts(update, context):
    text = update.message.text
    text = text.replace('/posts ', '')
    uid = text.split()[0]
    need_emotion = text.split()[1]
    logging.info(f'This is your wall: {uid}')
    logging.info(f'This is your emotion: {need_emotion}')
    try:
        posts = httpx.get(f'{backend_url}/api/v1/walls/{uid}/posts/?emotion={{{need_emotion}}}')
        update.message.reply_text('''Указанной эмоциональной окраске: {} \nCоответствуют комментарии:\n"{}"\n'''.format(need_emotion, posts.json()[0]['text']))
    except httpx.ConnectError:
        logging.info('Can\'t connect to backend')


def set_wall(update, context):
    text = update.message.text
    data = text.replace('/setwall', '').strip()
    regexp = re.compile(r"https://vk\.com/wall-(\d*)")
    matches = regexp.match(data)
    if not matches:
        update.message.reply_text('Введите стену в формате /setwall https://vk.com/wall-5678342')

    wall_id = str(matches.group()[0])
    payload = {
        "wall": wall_id,
        "link": "https://vk.com/wall-" + wall_id,
        "uid": "-1"
    }
    try:
        httpx.post(f'{backend_url}/api/v1/walls', json=payload)
        update.message.reply_text('Ваша стена отправлена на анализ')
    except httpx.ConnectError:
        logging.info("Can\'t connect to backend")

    logging.info(f'This is your text: {text}')
    logging.info(f'This is your link: {payload["link"]}')
    logging.info(f'This is your wall: {wall_id}')


def main():
    mybot = Updater(TOKEN, use_context=True)
    logging.basicConfig(level=logging.INFO)
    logging.info('TG bot has started')
    dp = mybot.dispatcher
    dp.add_handler(CommandHandler("setwall", set_wall))
    dp.add_handler(CommandHandler("predict", get_emotions))
    dp.add_handler(CommandHandler("posts", get_posts))
    dp.add_handler(CommandHandler("start", greet_user))
    dp.add_handler(CommandHandler("help", print_help))
    dp.add_handler(MessageHandler(Filters.text, default_response_to_user))
    mybot.start_polling()
    mybot.idle()


if __name__ == "__main__":
    main()
