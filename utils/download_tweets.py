"""
Downloads all the tweets of an event and add its to mongodb instance.
"""
from time import sleep

import tweepy
from pymongo import MongoClient
from sqlalchemy.orm import sessionmaker

from baselines.kmeans import filter_tweet
from db.engines import engine_lmartine as engine
from db.events import get_tweets
from db.models_new import EventGroup

consumer_key = "8EnRbS2eN4iRm3wkMNJsK9Eed"
consumer_secret = "lqAwxv2ajssv54z3jAKVAhVeQGKJzeKbCB8qFkfd6XVEYgDm1b"
access_token = "801140631955533824-TjpkQFuDLJduPjYhpnEKdR6sFHMqtn4"
access_token_secret = "U7XgsgC5JfTxOysZ2Yi1anJtqhNBfQDsWhKbFeLsA9Nlm"

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)

api = tweepy.API(auth)


def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]


if __name__ == '__main__':

    event_name = 'hurricane_irma2'

    Session = sessionmaker(engine, autocommit=True)
    session = Session()

    event = session.query(EventGroup).filter(EventGroup.name == event_name).first()
    ids = list(map(int, event.event_ids.split(',')))

    client = MongoClient()
    db = client.tweets_irma
    collection = db.tweets_collection

    tweets = get_tweets(event_name, ids, session)
    tweets_ids = [tweet.tweet_id for tweet in tweets if filter_tweet(tweet.text)]
    tweets_ids_unique = list(set(tweets_ids))

    chunks_tweets = chunks(tweets_ids, 150)
    count_request = 0
    count_inserted = 0
    print(len(tweets))
    print(len(tweets_ids_unique))
    remaining = 51
    limits_app = 91
    for chunk in chunks_tweets:
        if count_request % 10 == 0:
            limits_status = api.rate_limit_status()
            limits = limits_status['resources']['statuses']['/statuses/lookup']
            limits_app = limits_status['resources']['application']['/application/rate_limit_status']['remaining']
            remaining = limits['remaining']
            print('Peticiones restantes {}'.format(limits_app))
            print(remaining)

        if remaining > 10 and limits_app > 10:
            download_tweets = api.statuses_lookup(chunk, include_entities=True)
            count_request = count_request + 1
            tweets_json = [tweet._json for tweet in download_tweets]
            #last_id = tweets_json[len(tweets_json) - 1]['id']
            collection.insert_many(tweets_json)
            count_inserted = count_inserted + len(tweets_json)

        else:
            print("Pausa")
            sleep(1020)

    print(count_inserted)
