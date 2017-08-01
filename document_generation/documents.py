from document_generation.union_find import UnionFind
from typing import List, Dict
from tqdm import tqdm
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


def join_tweets(tweet_urls: Dict):
    """
    :param tweet_urls: dict tweet_id => [(tweet object, url object), ...]
    :return: list of lists of Tweet object ids
    """
    logger.info("Joining tweets by URL, RT or Reply")
    groups = defaultdict(list)
    uf = UnionFind()

    for tweet_id, tweet_url_list in tqdm(tweet_urls.items(), desc=f"join_tweets | Creating sets"):
        uf.make_set(tweet_id)

        for tweet, url in tweet_url_list:
            if tweet.retweet_of_id:
                uf.make_set(tweet.retweet_of_id)

            if tweet.in_reply_to_status_id:
                uf.make_set(tweet.in_reply_to_status_id)

            if url:
                uf.make_set(f"url_{url.id}")

    for tweet_id, tweet_url_list in tqdm(tweet_urls.items(), desc=f"join_tweets | Joining sets"):
        for tweet, url in tweet_url_list:
            if tweet.retweet_of_id:
                uf.union(tweet.tweet_id, tweet.retweet_of_id)
            if tweet.in_reply_to_status_id:
                uf.union(tweet.tweet_id, tweet.in_reply_to_status_id)
            if url:
                uf.union(tweet.tweet_id, f"url_{url.id}")

    for tweet_id, _ in tqdm(tweet_urls.items(), desc=f"join_tweets | Creating groups"):
        parent = uf.find(tweet_id)
        groups[parent].append(tweet_id)

    return list(groups.values())


def compute_groups_stats(groups: List[List[int]], tweet_urls: Dict):
    """
    :param groups: documents (list of lists of tweet ids)
    :param tweet_urls: dict tweet_id => tweet object + url_id
    :return:
    """

    stats = dict()
    for i, group in tqdm(enumerate(groups)):
        for tweet_id in group:
            tweet_url_list = tweet_urls[tweet_id]
            for tweet, _ in tweet_url_list:
                if i in stats:
                    stats[i] = {
                        'rt_count': stats[i]['rt_count'] + tweet.retweet_count,
                        'fav_count': stats[i]['fav_count'] + tweet.favorite_count,
                        'total_tweets': stats[i]['total_tweets'] + 1
                    }
                else:
                    stats[i] = {
                        'rt_count': tweet.retweet_count,
                        'fav_count': tweet.favorite_count,
                        'total_tweets': 1
                    }

    return stats


def get_representants(groups: List[List[int]], tweet_urls: Dict, w=(.8, .2)):
    """Selects tweets as representants from each document group.
    :param groups: documents (list of lists of tweet ids)
    :param tweet_urls: dict tweet_id => tweet object + url_id
    :param w: weights
    :return: Iterator: tweet_id for each document
    """
    logger.info("Getting representants from groups")
    for group in tqdm(groups):
        representant = None
        rep_score = 0
        for tweet_id in group:
            tweet_url_list = tweet_urls[tweet_id]
            for tweet, _ in tweet_url_list:
                if tweet.retweet_of_id:
                    continue
                score = w[0] * tweet.retweet_count + w[1] * tweet.favorite_count
                if score > rep_score:
                    representant = tweet_id
                    rep_score = score
            representant = representant or group[0]

        yield representant
