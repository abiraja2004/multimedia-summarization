"""
given event ids, get event info
"""

from typing import List
from db.models_cuboid import Tweet, TweetURL, URL
from collections import defaultdict

import logging

logger = logging.getLogger(__name__)


def get_tweets(event_name, event_ids: List[int], session, with_urls=True):
    logger.info(f"Event name: {event_name}")

    if with_urls:
        logger.info(f"Loading with URLs...")
        tweets = session.query(Tweet, URL)\
            .outerjoin(TweetURL, Tweet.tweet_id == TweetURL.tweet_id)\
            .outerjoin(URL, TweetURL.url_id == URL.id)\
            .filter(Tweet.event_id_id.in_(event_ids))\
            .all()
    else:
        tweets = session.query(Tweet).filter(Tweet.event_id_id.in_(event_ids)).all()

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


