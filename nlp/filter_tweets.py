"""
filters tweets based on simple heuristics
1. # of hashtags
2. # of urls
"""

from tqdm import tqdm
import logging
from typing import Dict
from db.models_new import *

from nlp.tokenizer import Tokenizer
logger = logging.getLogger(__name__)


def filter_tweets(tweets: Dict[int, Tweet],
                  tokenizer: Tokenizer,
                  max_hashtags: int = 2,
                  max_urls: int = 2) -> Dict[int, Tweet]:
    """
    :param tweets: list of tweets
    :param tokenizer:  nlp.tokenizer.Tokenizer
    :param max_hashtags: max hashtags allowed
    :param max_urls: max urls allowed
    :return: list of filtered pairs (tweet_obj, url_obj)
    """
    logger.info(f"Filtering out tweets with more than {max_hashtags} hashtags or {max_urls} urls")

    filtered_tweets = dict()
    for tweet_id, count in tqdm(zip(tweets.keys(),
                                    tokenizer.count_special_tokens([tweet.text for tweet in tweets.values()])),
                                desc="filter_tweets | Tokenizing tweets", total=len(tweets)):
        no_htg, no_url = count

        if no_htg <= max_hashtags and no_url <= max_urls:
            filtered_tweets[tweet_id] = tweets[tweet_id]

    logger.info(f"Ending up with {len(filtered_tweets)} (tweet, url) pairs")
    return filtered_tweets


