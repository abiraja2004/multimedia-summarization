from tqdm import tqdm
import logging

logger = logging.getLogger(__name__)


def get_representatives(tweets, url_tweets, urls):
    """
    Select representative tweets for each URL
    :return:
    """
    logger.info("Getting representative tweets")

    for clean_url, tweet_ids in tqdm(url_tweets.items(), total=len(url_tweets)):
        url_id = urls[clean_url]
        tweet_objs = [tweets[i] for i in tweet_ids if tweets.get(i)]
        non_rts = list(filter(lambda t_: not t_.retweeted_status_id, tweet_objs))

        # privilege earliest original tweet
        if non_rts:
            rep = min(non_rts, key=lambda t_: t_.created_at)
            tweet = rep

        else:
            # if there's only one tweet, yield it
            if len(tweet_objs) == 1:
                tweet = tweet_objs[0]

            # else, select the tweet with most RTs and likes
            elif len(tweet_objs) > 1:
                score = 0
                tweet = tweet_objs[0]
                for t in tweet_objs:
                    if t.retweet_count + t.favorite_count > score:
                        score = t.retweet_count + t.favorite_count
                        tweet = t

            else:
                continue

        if tweet:
            yield (url_id, clean_url, tweet)
