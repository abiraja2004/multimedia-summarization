"""
Transform tweets in db to items for MGraph and save them in mongoDB instance
"""
import json

from pymongo import MongoClient
from sqlalchemy.orm import sessionmaker
from tqdm import tqdm

from db import datasets
from db.engines import engine_lmartine as engine
from db.events import get_tweets
from db.models_new import TweetURL, ShortURL, User
from utils.download_tweets import chunks

client = MongoClient()


def insert_items(event_ids, event_name, session):
    db = client['tweets_' + event_name]
    collection = db['tweets_collection']
    data = transform(event_ids, event_name, session)
    chunks_tweets = chunks(data, 100)
    for chunk in tqdm(chunks_tweets):
        collection.insert_many(chunk)


def transform(event_ids, event_name, session):
    tweets = get_tweets(event_name, event_ids, session)
    print(len(tweets))
    data = []
    for tweet in tweets:
        item = create_item(tweet, session)
        data.append(item)
    return data


def create_item(tweet, session):
    item = {'_id': str(tweet.tweet_id), 'text': tweet.text, 'publicationTime': tweet.created_at,
            'reposts': tweet.retweet_count, 'original': tweet.is_a_retweet,
            'inReplyId': str(tweet.in_reply_to_status_id)}
    if tweet.is_a_retweet:
        item['reference'] = tweet.retweeted_status_id
        item['original'] = False
    else:
        item['original'] = True
    entities = json.loads(tweet.entities)
    user = session.query(User).filter(User.user_id == tweet.user_id).all()
    item['username'] = user.screen_name
    urls = session.query(ShortURL, TweetURL).outerjoin(TweetURL, ShortURL.id == TweetURL.url_id).filter(
        TweetURL.tweet_id == tweet.id).all()
    urls_list = []
    for url in urls:
        urls_list.append(url.short_url)
    item['urls'] = urls_list

    if 'media' in entities.keys():
        medias = entities['media']
        media_dict = {}
        for media in medias:
            media_dict[str(media['id'])] = media['media_url']
        item['media'] = media_dict

    text = tweet.text
    hashtags = [token for token in text.split(' ') if token.startswith('#')]
    item['hashtags'] = hashtags
    return item
    # item['entities'] = tweet.entities


if __name__ == '__main__':
    name = 'irma'
    ids = datasets.irma

    Session = sessionmaker(engine, autocommit=True)
    session = Session()

    insert_items(ids, name, session)
