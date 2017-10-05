"""
Transform tweets in db to items for MGraph and save them in mongoDB instance
"""
from pymongo import MongoClient

from db.events import get_tweet_ids, get_tweets_from_ids
from db.models_new import TweetURL, ShortURL
from utils.download_tweets import chunks

client = MongoClient()


def insert_items(event_ids, event_name, session):
    db = client['tweets_' + event_name]
    collection = db['tweets_collection']
    data = transform(event_ids, event_name, session)
    chunks_tweets = chunks(data, 100)
    for chunk in chunks_tweets:
        collection.insert_many(chunk)


def transform(event_ids, event_name, session):
    tweets_ids = get_tweet_ids(event_name, event_ids, session)
    tweets = get_tweets_from_ids(tweets_ids, tweets_ids)
    data = []
    for tweet in tweets:
        item = create_item(tweet, session)
        data.append(item)
    return data


def create_item(tweet, session):
    item = {'_id': tweet.tweet_id, 'text': tweet.text, 'publicationTime': tweet.created_at,
            'reposts': tweet.retweet_count, 'original': tweet.is_a_retweet, 'username': tweet.in_reply_to_screen_name,
            'inReplyId': tweet.in_reply_to_status_id}
    if tweet.is_a_retweet:
        item['reference'] = tweet.retweeted_status_id
    entities = tweet.entities._json

    urls = session.query(ShortURL, TweetURL).outerjoin(TweetURL, ShortURL.id == TweetURL.url_id).filter(
        TweetURL.tweet_id == tweet.id).all()
    urls_list = []
    for url in urls:
        urls_list.append(url.short_url)
    item['urls'] = urls_list

    medias = entities['media']
    media_dict = {}
    for media in medias:
        media_dict[media['id']] = media['media_url']
    item['media'] = media_dict
    text = tweet.text
    hashtags = [token for token in text.split(' ') if token.startswith('#')]
    item['hashtags'] = hashtags
    return item
    # item['entities'] = tweet.entities
