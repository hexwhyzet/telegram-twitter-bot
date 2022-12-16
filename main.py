import datetime
import logging
import os
from collections import defaultdict
from pathlib import Path
from uuid import uuid4

from dotenv import load_dotenv
from pyrogram import Client, filters
from pyrogram.types import (InlineQueryResultPhoto)

from dataloader import DataLoader, AVATAR_PATH
from s3_exporter import get_resource_url, BUCKET, IMAGE_EXTENSION
from search_tweets import WhooshTwitterStorage
from tools import get_reply_targets, get_remaining_text, saved_id_to_image
from tweet_renderer import render_tweet

load_dotenv()

logs_path = 'logs'
logs_filename = 'log_file.log'
Path(logs_path).mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(logs_path + '/' + logs_filename, mode='a+', encoding='utf-8'),
        logging.StreamHandler()
    ],
)
logger = logging.getLogger(__name__)

data_loader = DataLoader()

api_id = os.getenv('TELEGRAM_API_ID')
api_hash = os.getenv('TELEGRAM_API_HASH')
bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
owner_username = os.getenv('TELEGRAM_OWNER_USERNAME')

session_path = 'session'
client_name = os.getenv('TELEGRAM_CLIENT_NAME')
Path(session_path).mkdir(parents=True, exist_ok=True)
app = Client(client_name,
             api_id=api_id,
             api_hash=api_hash,
             bot_token=bot_token,
             workdir=session_path)

indexer_path = 'indexer'
Path(indexer_path).mkdir(parents=True, exist_ok=True)
storage = WhooshTwitterStorage(indexer_path, data_loader.tweets)

session_stats = defaultdict(int)


@app.on_inline_query()
async def inline(_, inline_query):
    session_stats[inline_query.from_user.id] += 1
    tweet_search_results = []
    logger.info(f'Query {inline_query.id} from {inline_query.from_user.id}: {inline_query.query}')
    for i, search_result in enumerate(storage.search(inline_query.query, limit=20)):
        tweet_text = search_result['text']
        image_url = get_resource_url(BUCKET, f'tweets/{search_result["id"]}{IMAGE_EXTENSION}')
        tweet_hint = InlineQueryResultPhoto(
            photo_url=image_url,
            photo_width=search_result['render_width'],
            photo_height=search_result['render_height'],
            title=get_reply_targets(tweet_text),
            description=' '.join(get_remaining_text(tweet_text).split()),
        ),
        tweet_search_results.append(tweet_hint[0])
    await app.answer_inline_query(
        inline_query_id=inline_query.id,
        is_gallery=False,
        cache_time=1,
        results=tweet_search_results,
    )


@app.on_message(filters.user(owner_username) & filters.command("stats"))
def stats(_, message):
    message.reply(f"Unique users: {len(session_stats.keys())}\nRequests: {sum(session_stats.values())}")


@app.on_message(filters.command("help") | filters.command("start"))
def stats(_, message):
    message.reply(f"<b>Привет, это НеИлонБот!</b>\n\n"
                  f"/g или /gen или /generate – создать твит от лица Илона\n\n"
                  f"Чтобы искать по существующим твитам, то введите @notelonbot в поле набора сообщения а дальше "
                  f"вводите строку строку по который вы хотите найти твит Илона Маска (не все они настоящие). "
                  f"Данную манипуляцию можно делать в любом чате телеграмма!")


@app.on_message(filters.command("g") | filters.command("gen") | filters.command("generate"))
def generate(client, message):
    image_path = f"tmp/{uuid4()}.jpeg"
    text_body = " ".join(message.text.split()[1:])
    if not len(text_body):
        message.reply(f"Строка после команды не может быть пустой, попробуйте дописать какое-нибудь слово")
        return
    render_tweet(
        data_loader.profile.username,
        data_loader.profile.name,
        text_body,
        datetime.datetime.now(),
        AVATAR_PATH,
        False,
        image_path,
        "tweet_template.html",
    )
    client.send_photo(message.chat.id, image_path)


logger.info('Bot started polling!')
app.run()
