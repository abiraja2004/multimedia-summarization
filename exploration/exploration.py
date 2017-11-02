from sqlalchemy.orm import sessionmaker

from db import datasets
from db.engines import engine_lmartine as engine
from db.events import get_tweets_and_urls


def exploration(event_name, ids, session):
    tweets, urls, tweets_urls, urls_tweets = get_tweets_and_urls(event_name, ids, session)
    print(len(tweets.keys()))
    print(len(urls.keys()))
    avg_url = 0
    for _, tweets_ids in tweets_urls.items():
        avg_url = + len(tweets_ids)

    avg_url = avg_url / len(urls.keys())

    originals = 0
    retweets = 0
    users = {}
    for _, tweet in tweets:
        users[tweet.user_id] = 1
        if tweet.is_a_retweet:
            retweets = + 1
        else:
            originals = + 1
    print(retweets)
    print(originals)


if __name__ == '__main__':
    Session = sessionmaker(engine, autocommit=True)
    session = Session()
    event_name = 'irma'
    ids = datasets.irma
    exploration(event_name, ids, session)
