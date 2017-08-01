"""
filters tweets based on simple heuristics
1. # of hashtags
2. # of urls
"""

from tqdm import tqdm
import logging
logger = logging.getLogger(__name__)


def filter_tweets(tweet_url, tokenizer, max_hashtags=2, max_urls=3):
    """
    :param tweet_url: list of pairs (tweet_obj, url_obj)
    :param tokenizer:  nlp.tokenizer.Tokenizer
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


