import asyncio
import locale
import os.path
from datetime import datetime

from jinja2 import FileSystemLoader, Environment
from pyppeteer import launch

from tools import get_reply_targets, get_remaining_text, parse_tweet_datetime

DEFAULT_RESOURCES_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "resources")
DEFAULT_TWEET_TEMPLATE = "tweet_template.html"
RENDERED_TWEET_TEMPLATE = os.path.join(DEFAULT_RESOURCES_DIR, "rendered_tweet_template.html")


async def render_tweet_html(source, destination, tweet_elem_id):
    browser = await launch({"handleSIGINT": False, "handleSIGTERM": False, "handleSIGHUP": False},
                           headless=True, args=['--no-sandbox'])
    page = await browser.newPage()
    await page.setViewport({'width': 1000, 'height': 1000, 'deviceScaleFactor': 2})
    await page.goto("file:" + source)

    tweet = await page.querySelector(tweet_elem_id)
    tweet_box = await tweet.boundingBox()
    x = tweet_box['x']
    y = tweet_box['y']
    w = tweet_box['width']
    h = tweet_box['height']

    await page.screenshot({'path': destination, 'clip': {'x': x, 'y': y, 'width': w, 'height': h}})
    await browser.close()


def redner_tweet_reply(reply_targets):
    def get_plural_ending(num: int):
        if num % 10 == 1 and num % 100 != 11:
            return 'ю'
        return 'ям'

    replies_num = len(reply_targets.split())
    tweet_reply = ""
    if replies_num <= 2:
        if replies_num == 1:
            tweet_reply += reply_targets.split()[0]
        elif replies_num == 2:
            tweet_reply += " и ".join(reply_targets.split())
    else:
        tweet_reply += " ".join(
            reply_targets.split()[:1]) + f" и еще {replies_num - 1} пользовател{get_plural_ending(replies_num - 1)}"

    return tweet_reply


def render_tweet_time(dt: datetime):
    return dt.strftime('%-H:%M')


def render_tweet_date(dt: datetime):
    locale.setlocale(locale.LC_ALL, ('ru_RU', 'UTF-8'))
    return dt.strftime('%-d %b. %Y г.')


def render_tweet(username: str, name: str, text: str, created_at: datetime, avatar_path: str, verified: bool,
                 result_path, tweet_template: str = DEFAULT_TWEET_TEMPLATE):
    reply_targets = get_reply_targets(text)
    remaining_text = get_remaining_text(text)

    template_loader = FileSystemLoader(searchpath=DEFAULT_RESOURCES_DIR)
    template_env = Environment(loader=template_loader)
    template = template_env.get_template(tweet_template)
    context = {
        "tweet_avatar": avatar_path,
        "tweet_username": username,
        "tweet_name": name,
        "tweet_message": remaining_text,
        "tweet_verified": verified,
        "tweet_reply": redner_tweet_reply(reply_targets),
        "tweet_time": render_tweet_time(created_at),
        "tweet_date": render_tweet_date(created_at),
    }

    output = template.render(context)
    with open(RENDERED_TWEET_TEMPLATE, "w+", encoding="utf-8") as file:
        file.write(output)

    loop = asyncio.new_event_loop()
    loop.run_until_complete(render_tweet_html(RENDERED_TWEET_TEMPLATE, result_path, '#tweet_box'))
