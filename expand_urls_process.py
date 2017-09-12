from document_generation import expand_urls
from db.models_new import Tweet, TweetURL, URL
from db.engines import engine_of215 as engine
from tqdm import tqdm
from sqlalchemy.orm import sessionmaker
import logging
import spacy


logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s | %(name)s | %(levelname)s : %(message)s', level=logging.INFO)
Session = sessionmaker(engine, autocommit=True)

session = Session()
nlp = spacy.load('en', parser=False, tagger=False, entity=False, matcher=False)
batch_size = 10000
n_threads = 64
# 18:38

# esto no es lindo:
tweets = []
for tweet in session.query(Tweet).filter(~Tweet.url_expanded).yield_per(batch_size):
    tweets.append(tweet)

    if len(tweets) < batch_size:
        continue
    else:
        logger.info(f"read {batch_size} tweets")
        info, short_tweet = expand_urls.expand_urls(nlp, tweets, n_threads=n_threads)
        info_items = list(info.items())
        # exp[short] = (long, title, clean_long)

        logger.info(f"saving {len(info_items)} new urls")
        # esto tampoco
        urls_to_save = []
        with session.begin():
            for short, (expanded, title, clean) in tqdm(info_items):
                url = URL(short_url=short,
                          expanded_url=expanded,
                          title=title,
                          expanded_clean=clean)
                session.add(url)
                urls_to_save.append(url)

        with session.begin():
            for url, (short, _) in tqdm(list(zip(urls_to_save, info_items))):
                tweet_ids = short_tweet[short]
                for tweet_id in tweet_ids:
                    tweet_url = TweetURL(tweet_id=tweet_id, url_id=url.id)
                    session.add(tweet_url)

        with session.begin():
            for _tweet in tweets:
                _tweet.url_expanded = True

        tweets = []
        logger.info("done")





