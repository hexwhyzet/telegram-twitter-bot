import json
import re
from datetime import datetime

from PIL import Image


def get_reply_targets(text):
    match = re.match(r"(@\S+\s)+", text)
    if match is None:
        return ""
    else:
        return match.group().strip()


def get_remaining_text(text):
    return text.removeprefix(get_reply_targets(text)).strip()


def parse_tweet_datetime(created_at):
    return datetime.fromisoformat(created_at.removesuffix("Z"))


def saved_tweets():
    return json.loads(open('data_old/tweets/199714122.json', 'r').read())


def saved_id_to_image():
    return json.loads(open('data_old/id_to_image.json', 'r').read())


def get_width_height(path):
    im = Image.open(path)
    return im.size
