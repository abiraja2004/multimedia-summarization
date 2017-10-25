"""
given event ids, get event info
"""

from typing import List
from db.models_new import *
from collections import defaultdict
from typing import Dict
from tqdm import tqdm

import logging

logger = logging.getLogger(__name__)


"""
search by keyword in DB

set @k = "irma";
select *
from event_2017 
where 
 keyword1 like concat("%", @k, "%") collate utf8mb4_unicode_520_ci 
 or keyword2 like concat("%", @k, "%") collate utf8mb4_unicode_520_ci
 or keyword3 like concat("%", @k, "%") collate utf8mb4_unicode_520_ci;
"""


def get_tweets(event_name: str, event_ids: List[int], session, filtering=False):
    logger.info(f"Event name: {event_name}")

    tweets = dict()
    tweet_objs = session.query(Tweet).yield_per(50000)\
        .join(EventTweet, Tweet.tweet_id == EventTweet.tweet_id)\
        .filter(EventTweet.event_id.in_(event_ids))

    if filtering:
        tweet_objs = tweet_objs.filter(Tweet.is_filtered)
        tweets = tweet_objs.all()
        logger.info(f"Loaded {len(tweets)} tweets")
        return tweets

    if not filtering:
        for tweet in tqdm(tweet_objs, desc="removing duplicates"):
            tweets[tweet.tweet_id] = tweet

        logger.info(f"Loaded {len(tweets)} tweets")
        return list(tweets.values())


def get_tweets_and_urls(event_name: str, event_ids: List[int], session, filtering=False, yield_per=50000):
    logger.info(f"Event name: {event_name}")

    query = session.query(Tweet, ExpandedURL)\
        .yield_per(yield_per)\
        .join(EventTweet, EventTweet.tweet_id == Tweet.tweet_id)\
        .outerjoin(TweetURL, TweetURL.tweet_id == Tweet.tweet_id)\
        .join(ShortURL, ShortURL.id == TweetURL.url_id)\
        .join(ExpandedURL, ExpandedURL.id == ShortURL.expanded_id)\
        .filter(EventTweet.event_id.in_(event_ids))

    if filtering:
        query = query.filter(Tweet.is_filtered)

    tweets = dict()
    urls = dict()
    tweet_url = dict()
    url_tweets = defaultdict(set)

    for tweet, url in tqdm(query):
        tweets[tweet.tweet_id] = tweet
        urls[url.id] = url
        tweet_url[tweet.tweet_id] = url.id
        url_tweets[url.id].add(tweet.tweet_id)

    return tweets, urls, tweet_url, url_tweets


def get_tweet_ids(event_name: str, event_ids: List[int], session):
    logger.info(f"Event name: {event_name}")

    tweet_ids = session.query(Tweet.tweet_id).distinct().yield_per(1000)\
        .join(EventTweet, Tweet.tweet_id == EventTweet.tweet_id)\
        .filter(EventTweet.event_id.in_(event_ids))\
        .all()

    logger.info(f"Loaded {len(tweet_ids)} tweets")
    return tweet_ids


def get_urls(tweets: List[Tweet], session, chunk_size=1):
    def chunks(l, n):
        """Yield successive n-sized chunks from l."""
        for i in range(0, len(l), n):
            yield l[i:i + n]

    all_urls = dict()
    tweet_urls = dict()

    for tweet_chunk in tqdm(chunks(tweets, chunk_size), total=len(tweets) / chunk_size, desc="querying urls"):
        tweet_ids = [tweet.tweet_id for tweet in tweet_chunk]

        tweet_url = session.query(TweetURL)\
            .filter(TweetURL.tweet_id.in_(tweet_ids))\
            .all()

        urls = session.query(ExpandedURL)\
            .join(ShortURL, ShortURL.expanded_id == ExpandedURL.id)\
            .join(TweetURL, ShortURL.id == TweetURL.url_id)\
            .filter(TweetURL.tweet_id.in_(tweet_ids))\
            .all()

        for url in urls:
            all_urls[url.id] = url

    return all_urls


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


def set_filtered_tweets(tweets: Dict[int, Tweet], session):
    with session.begin():
        for tweet_id, tweet in tqdm(tweets.items(), desc="setting filtered status on tweets"):
            db_tweet = session.query(Tweet).filter(Tweet.tweet_id == tweet_id).first()
            db_tweet.is_filtered = True


def save_documents(representatives: List[Tweet],
                   url_tweets: Dict[int, List[int]],
                   tweets: Dict[int, Tweet],
                   event: EventGroup,
                   session):

    with session.begin():
        docs = []

        for rep, (url_id, tweet_ids) in tqdm(zip(representatives, url_tweets.items()),
                                             desc="Creating/saving documents",
                                             total=len(representatives)):
            total_replies = 0
            for tw_id in tweet_ids:
                tweet = tweets[tw_id]
                if tweet.in_reply_to_screen_name or tweet.in_reply_to_status_id or tweet.in_reply_to_user_id:
                    total_replies += 1

            doc = Document(text=rep.text,
                           tweet_id=rep.tweet_id,
                           total_rts=rep.retweet_count,
                           total_favs=rep.favorite_count,
                           total_replies=total_replies,
                           total_tweets=len(tweet_ids),
                           embedded_html=None,
                           expanded_url_id=url_id)

            session.add(doc)
            docs.append(doc)

    with session.begin():
        for doc, (_, tweet_ids) in tqdm(zip(docs, url_tweets.items()),
                                        desc="Saving assoc documents", total=len(docs)):
            doc_ev = DocumentGroup(document_id=doc.id,
                                   eventgroup_id=event.id)

            session.add(doc_ev)

            for tw_id in tweet_ids:
                doc_tw = DocumentTweet(document_id=doc.id,
                                       tweet_id=tw_id)

                session.add(doc_tw)


def get_documents_from_event(name: str, session):
    documents = session.query(Document, Tweet)\
        .join(DocumentGroup, DocumentGroup.document_id == Document.id)\
        .join(EventGroup, EventGroup.id == DocumentGroup.eventgroup_id)\
        .join(Tweet, Document.tweet_id == Tweet.tweet_id)\
        .filter(EventGroup.name == name).all()
    return documents


