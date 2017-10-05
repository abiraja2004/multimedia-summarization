from document_generation.union_find import UnionFind
from typing import List, Dict, Any
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

    return list([group for group in groups.values() if len(group) > 1])


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


def get_representatives(url_tweets: Dict[int, List[int]], tweets: Dict[int, Any]):
    """
    Select representative tweets for each URL
    :param url_tweets:
    :param tweets:
    :param weights:
    :return:
    """
    logger.info("Getting representative tweets")

    for url, tweet_ids in tqdm(url_tweets.items(), total=len(url_tweets)):
        tweet_objs = [tweets[id_] for id_ in tweet_ids]
        non_rts = list(filter(lambda t_: not t_.is_a_retweet, tweet_objs))

        # privilege earliest original tweet
        if non_rts:
            rep = min(non_rts, key=lambda t_: t_.created_at)
            yield rep

        else:
            # if there's only one tweet, yield it
            if len(tweet_objs) == 1:
                yield tweet_objs[0]

            # else, select the tweet with most RTs and likes
            else:
                score = 0
                tweet = tweet_objs[0]
                for t in tweet_objs:
                    if t.retweet_count + t.favorite_count > score:
                        score = t.retweet_count + t.favorite_count
                        tweet = t

                yield tweet
