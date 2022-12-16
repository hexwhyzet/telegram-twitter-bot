import hashlib
import os
from dataclasses import dataclass, asdict
from json import loads, dumps
from os import path
from typing import List
from uuid import uuid4

from libs.hashing import sha256sum
from libs.singleton import Singleton
from s3_exporter import upload_tweet_render, delete_tweet_render
from tools import parse_tweet_datetime, get_width_height
from tweet_renderer import render_tweet
from twitter_api import get_tweet


@dataclass
class Profile:
    username: str
    name: str


@dataclass
class Tweet:
    id: str
    verified: bool
    created_at: str
    text: str
    render_width: int
    render_height: int
    original_id: int = None


ID_TO_IMAGE_PATH = "./data/id_to_image.json"
SAVED_TWEETS_PATH = "data/tweets.json"
AVATAR_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), "resources/assets/avatar.jpeg")


def read_tweets(file_path) -> List[Tweet]:
    raw_tweets = loads(open(file_path, "r").read())
    return [Tweet(**x) for x in raw_tweets]


def write_tweets(file_path, tweets):
    open(file_path, "w+").write(
        dumps([asdict(tweet) for tweet in tweets])
    )


class DataLoader(metaclass=Singleton):
    def __init__(self):
        profile_json = loads(open("config/profile.json", "r").read())
        self.profile = Profile(
            username=profile_json["username"],
            name=profile_json["name"],
        )

        avatar_hash = sha256sum(AVATAR_PATH)
        raw_tweets_json = loads(open("config/tweets.json", "r").read())

        saved_tweets = list()
        if path.exists(SAVED_TWEETS_PATH):
            saved_tweets = read_tweets(SAVED_TWEETS_PATH)

        rendered_ids = set(map(lambda x: x.id, saved_tweets))
        current_used_ids = set()
        new_saved_tweets_json = list()
        for raw_tweet_json in raw_tweets_json:
            original_id = None
            if isinstance(raw_tweet_json, int):
                original_id = raw_tweet_json
                tweet_json = get_tweet(original_id)
                text = tweet_json["text"]
                created_at = tweet_json["created_at"]
                verified = True
            else:
                text = raw_tweet_json["text"]
                created_at = raw_tweet_json["created_at"]
                verified = False

            tweet_id = hashlib.sha256(str.encode(
                text + created_at + avatar_hash + self.profile.username + self.profile.name + str(
                    verified))).hexdigest()

            current_used_ids.add(tweet_id)
            tmp_filename = f"./tmp/{uuid4()}.jpeg"
            if tweet_id not in rendered_ids:
                render_tweet(
                    username=self.profile.username,
                    name=self.profile.name,
                    text=text,
                    created_at=parse_tweet_datetime(created_at),
                    result_path=tmp_filename,
                    avatar_path=AVATAR_PATH,
                    verified=verified
                )
                upload_tweet_render(tweet_id, tmp_filename)
                width, height = get_width_height(tmp_filename)
                os.remove(tmp_filename)
                new_saved_tweets_json.append(
                    Tweet(
                        id=tweet_id,
                        text=text,
                        created_at=created_at,
                        verified=verified,
                        original_id=original_id,
                        render_width=width,
                        render_height=height,
                    )
                )
            else:
                new_saved_tweets_json.append(list(filter(lambda x: x.id == tweet_id, saved_tweets))[0])
        unavailable_tweets = rendered_ids - current_used_ids
        for tweet_id_to_delete in unavailable_tweets:
            delete_tweet_render(tweet_id_to_delete)

        self.tweets = new_saved_tweets_json
        write_tweets(SAVED_TWEETS_PATH, new_saved_tweets_json)
