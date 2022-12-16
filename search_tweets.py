import os.path
from abc import ABC
from datetime import datetime
from typing import List

from whoosh.fields import Schema, TEXT, DATETIME, NUMERIC
from whoosh.index import create_in
from whoosh.qparser import QueryParser
from whoosh.query import FuzzyTerm

from dataloader import Tweet

TWEET_SCHEMA = Schema(
    id=TEXT(stored=True),
    text=TEXT(stored=True),
    created_at=DATETIME(stored=True),
    render_width=NUMERIC(bits=64, stored=True),
    render_height=NUMERIC(bits=64, stored=True),
)


class MyFuzzyTerm(FuzzyTerm, ABC):
    def __init__(self, fieldname, text, boost=1.0, maxdist=1, prefixlength=1, constantscore=True):
        super(MyFuzzyTerm, self).__init__(fieldname, text, boost, maxdist, prefixlength, constantscore)


class WhooshTwitterStorage:
    def __init__(self, path, tweets: List[Tweet]):
        if not os.path.exists(path):
            os.mkdir(path)
        self.ix = create_in(path, TWEET_SCHEMA)
        self.writer = self.ix.writer()
        for tweet in tweets:
            self.writer.add_document(
                id=tweet.id,
                text=tweet.text,
                created_at=datetime.fromisoformat(tweet.created_at[:-1]),
                render_width=tweet.render_width,
                render_height=tweet.render_height,
            )
        self.writer.commit()

    def search(self, text, limit=10):
        searcher = self.ix.searcher()
        search_field = 'text'
        parser = QueryParser(search_field, self.ix.schema, termclass=MyFuzzyTerm)
        query = parser.parse(text)
        results = searcher.search(query, limit=limit)
        return results
