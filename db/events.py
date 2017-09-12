"""
given event ids, get event info
"""

from typing import List
from db.models_new import *
from collections import defaultdict
from typing import Iterable
from tqdm import tqdm

import logging

logger = logging.getLogger(__name__)


def get_tweets(event_name: str, event_ids: List[int], session, with_urls=True):
    logger.info(f"Event name: {event_name}")

    if not with_urls:
        tweets = session.query(Tweet)\
            .join(EventTweet, Tweet.tweet_id == EventTweet.tweet_id)\
            .filter(EventTweet.event_id.in_(event_ids))\
            .all()
    else:
        tweets = session.query(Tweet, URL)\
            .join(EventTweet, Tweet.tweet_id == EventTweet.tweet_id)\
            .outerjoin(TweetURL, Tweet.tweet_id == TweetURL.tweet_id)\
            .outerjoin(URL, TweetURL.url_id == URL.id)\
            .filter(EventTweet.event_id.in_(event_ids))\
            .all()

    logger.info(f"Loaded {len(tweets)} tweets")
    return tweets


def create_tweet_urls_dict(tweet_urls):
    """
    creates a dictionary
    tweet_id => [(tweet_obj, url_obj), ...]
    :param tweet_urls:
    :return: defaultdict
    """
    logger.info("Creating dict t.id => [(t, u), ...]")
    data = defaultdict(list)
    for tweet, url in tweet_urls:
        data[tweet.tweet_id].append((tweet, url))
    return data


def get_tweets_from_ids(tweet_ids, session):
    """
    returns tweet objects from list of ids
    :param tweet_ids: list of integers
    :param session: the session
    :return: list of tweet objects
    """

    tweets = session.query(Tweet).filter(Tweet.tweet_id.in_(tweet_ids)).all()
    return tweets


def set_filtered_tweets(tweets: Iterable[Tweet], session):
    db_tweets = session.query(Tweet)\
        .filter(Tweet.tweet_id.in_([t.tweet_id for t, _ in tweets]))\
        .all()
    for tweet in tqdm(db_tweets, desc="Setting is_filtered in DB"):
        tweet.is_filtered = True
    session.commit()



