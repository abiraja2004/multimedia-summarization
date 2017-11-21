"""
Transform tweets in db to items for MGraph and save them in mongoDB instance
"""
import json

from pymongo import MongoClient
from sqlalchemy.orm import sessionmaker
from tqdm import tqdm

from db.engines import connect_to_server
from db.events import get_tweets
from db.models_new import User, Tweet, EventGroup
from utils.download_tweets import chunks

client = MongoClient()


def insert_items(event_ids, event_name, session):
    db = client[event_name]
    collection = db['tweets_collection']
    data = transform(event_ids, event_name, session)
    chunks_tweets = chunks(data, 100)
    for chunk in tqdm(chunks_tweets):
        collection.insert_many(chunk)


def transform(event_ids, event_name, session):
    tweets_full = get_tweets(event_name, event_ids, session, filtering=True)
    tweets = tweets_full[200000:300000]
    del tweets_full
    data = []
    for tweet in tqdm(tweets):
        item = create_item_mgraph(tweet, session)
        data.append(item)
    return data


def create_item_mgraph(tweet, session):
    item = {'id': str(tweet.tweet_id), 'text': tweet.text, 'created_at': str(tweet.created_at),
            'entities': json.loads(tweet.entities),
            'in_reply_to_status_id_str': str(tweet.in_reply_to_status_id), 'lang': 'en'}
    user = session.query(User).filter(User.user_id == tweet.user_id).first()
    user_dict = user.__dict__
    user_dict.pop('_sa_instance_state')
    item['user'] = user_dict
    if tweet.retweeted_status_id:
        rttweet = session.query(Tweet).filter(Tweet.id == tweet.retweeted_status_id).first()
        item['retweeted_status'] = rttweet.__dict__
    return item


if __name__ == '__main__':
    name = 'hurricane_irma2'

    connect = lambda: connect_to_server(username="lmartinez", host="172.17.69.88", ssh_pkey="/home/luis/.ssh/id_rsa")
    with connect() as engine:
        Session = sessionmaker(engine, autocommit=True)
        session = Session()

        event = session.query(EventGroup).filter(EventGroup.name == name).first()
        ids = list(map(int, event.event_ids.split(',')))

        insert_items(ids, name, session)
