"""
Downloads all the tweets of an event and add its to mongodb instance.
"""
from time import sleep

import tweepy
from pymongo import MongoClient

from db import datasets
from db.events import get_tweets
from main import session

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


event_name = "nepal_earthquake"
events_id = datasets.nepal_earthquake

client = MongoClient()
db = client.tweets_nepal
collection = db.tweets_collection

tweets = get_tweets(event_name, events_id, session)
tweets_ids = [tweet.tweet_id for tweet in tweets]

chunks = chunks(tweets_ids, 100)
count_request = 0
count_inserted = 0
print(len(tweets_ids))
for chunk in chunks:
    if count_request % 10 == 0:
        limits_status = api.rate_limit_status()
        limits = limits_status['resources']['users']['/users/lookup']
        limits_app = limits_status['resources']['application']['/application/rate_limit_status']['remaining']
        remaining = limits['remaining']
        print('Peticiones restantes {}'.format(limits_app))
    if remaining > 50 and limits_app > 90:
        download_tweets = api.statuses_lookup(chunk, include_entities=True)
        count_request = count_request + 1
        tweets_json = [tweet._json for tweet in download_tweets]
        collection.insert_many(tweets_json)
        count_inserted = count_inserted + len(tweets_json)
    else:
        print("Pausa")
        sleep(1020)

print(count_inserted)
print(count_request)
