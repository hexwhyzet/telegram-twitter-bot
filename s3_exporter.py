import os

import boto3
from dotenv import load_dotenv

load_dotenv()

BUCKET = os.getenv('S3_BUCKET')
IMAGE_EXTENSION = '.jpeg'


def get_client():
    session = boto3.session.Session()
    s3 = session.client(
        service_name='s3',
        endpoint_url='https://storage.yandexcloud.net'
    )
    return s3


def get_tweet_key(tweet_id) -> str:
    return 'tweets/' + str(tweet_id) + IMAGE_EXTENSION


def upload_tweet_render(tweet_id, render_path):
    s3 = get_client()
    s3.upload_file(
        render_path, BUCKET, get_tweet_key(tweet_id),
    )


def delete_tweet_render(tweet_id):
    s3 = get_client()
    s3.delete_object(
        Bucket=BUCKET, Key=get_tweet_key(tweet_id),
    )


def does_tweet_exists(tweet_id) -> bool:
    s3 = get_client()
    res = s3.list_objects_v2(Bucket=BUCKET, Prefix=get_tweet_key(tweet_id), MaxKeys=1)
    return 'Contents' in res


def get_resource_url(bucket, key) -> str:
    return f"https://storage.yandexcloud.net/{bucket}/{key}"
