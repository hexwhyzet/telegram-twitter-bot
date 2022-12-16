import json
import os

import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://api.twitter.com"
BEARER = os.getenv('TWITTER_BEARER')

PROXY_IP = os.getenv("PROXY_IP")
PROXY_PORT = os.getenv("PROXY_PORT")
proxies = {}
if PROXY_IP and PROXY_PORT:
    proxies = {
        'http': f'http://{PROXY_IP}:{PROXY_PORT}',
        'https': f'https://{PROXY_IP}:{PROXY_PORT}',
    }


def get_tweet(tweet_original_id: int):
    url = f"{BASE_URL}/2/tweets/{tweet_original_id}"
    params = {
        "tweet.fields": "created_at",
    }
    return json.loads(requests.get(url,
                                   params=params,
                                   headers={'Authorization': f'Bearer {BEARER}'},
                                   proxies=proxies).content)


def get_tweets(user_id: int, next_token=None):
    url = f"{BASE_URL}/2/users/{user_id}/tweets"
    params = {
        "max_results": 100,
        "exclude": "retweets",
        "tweet.fields": "created_at",
    }
    if next_token is not None:
        params["pagination_token"] = next_token
    return json.loads(requests.get(url,
                                   params=params,
                                   headers={'Authorization': f'Bearer {BEARER}'},
                                   proxies=proxies).content)


def dump_all_tweets(user_id: int, start_with_next_token=None, limit=100):
    last_tweets = []

    while True:
        response = get_tweets(user_id, start_with_next_token)
        last_tweets += response["data"]
        if len(last_tweets) >= limit or "next_token" not in response["meta"]:
            return last_tweets[:limit]
        start_with_next_token = response["meta"]["next_token"]
