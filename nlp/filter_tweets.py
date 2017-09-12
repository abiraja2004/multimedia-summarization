"""
filters tweets based on simple heuristics
1. # of hashtags
2. # of urls
"""

from tqdm import tqdm
import logging
from typing import Iterable, Tuple
from db.models_new import *

from nlp.tokenizer import Tokenizer
logger = logging.getLogger(__name__)


def filter_tweets(tweet_url: Iterable[Tuple[Tweet, URL]],
                  tokenizer: Tokenizer,
                  max_hashtags: int = 2,
                  max_urls: int = 2) -> Iterable[Tuple[Tweet, URL]]:
    """
    :param tweet_url: list of pairs (tweet_obj, url_obj)
    :param tokenizer:  nlp.tokenizer.Tokenizer
    :param max_hashtags: max hashtags allowed
    :param max_urls: max urls allowed
    :return: list of filtered pairs (tweet_obj, url_obj)
    """
    logger.info(f"Filtering out tweets with more than {max_hashtags} hashtags or {max_urls} urls")

    to_remove = []
    for i, count in tqdm(enumerate(tokenizer.count_special_tokens([tweet.text for tweet, _ in tweet_url])),
                         desc="filter_tweets | Tokenizing tweets", total=len(tweet_url)):
        no_htg, no_url = count

        if no_htg > max_hashtags or no_url > max_urls:
            to_remove.append(i)

    filtered_tweets = [(tweet, url) for i, (tweet, url) in enumerate(tweet_url) if i not in to_remove]
    logger.info(f"Ending up with {len(filtered_tweets)} (tweet, url) pairs")
    return filtered_tweets


