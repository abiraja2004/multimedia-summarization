import re
from pathlib import Path

from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import pairwise_distances_argmin_min
from sqlalchemy.orm import sessionmaker

import settings
from db.engines import engine_lmartine as engine
from db.events import get_tweets
from db.models_new import EventGroup
from evaluation.automatic_evaluation import remove_and_steam


def clean_tweet(tweet):
    return ' '.join(remove_and_steam(re.sub(r"@\w+", '', re.sub(r"http\S+", '', tweet.text.replace('#', ''))), False))


def clustering(n_clusters, event_name, event_ids, session):
    tweets = get_tweets(event_name, event_ids, session)
    clean_tweets = [(tweet.text, clean_tweet(tweet)) for tweet in tweets]
    vectorizer = TfidfVectorizer()
    tfidf = vectorizer.fit_transform([clean[1] for clean in clean_tweets])
    km = KMeans(n_clusters=n_clusters)
    km.fit(tfidf)


    closest, _ = pairwise_distances_argmin_min(km.cluster_centers_, tfidf)
    tokens_closest = []
    tweet_closest = []
    for close_index in closest:
        tokens_closest.append(vectorizer.inverse_transform(tfidf[close_index]))
        tweet_closest.append(tweets[close_index])
    return tweet_closest


def save_ids(tweets, event_name, n_clusters):
    with Path(settings.LOCAL_DATA_DIR_2, 'data', event_name, 'summaries', 'system',
              f'kmeans_centroid_{n_clusters}.txt').open('w') as summary:
        tweet_ids = [str(tweet.tweet_id) + '\n' for tweet in tweets]
        summary.writelines(tweet_ids)

if __name__ == '__main__':
    event_name = 'libya_hotel'

    Session = sessionmaker(engine, autocommit=True)
    session = Session()

    n_clusters = [10, 15, 20]
    event = session.query(EventGroup).filter(EventGroup.name == event_name).first()
    ids = list(map(int, event.event_ids.split(',')))

    for n in n_clusters:
        tweets = clustering(n, event_name, ids, session)
        save_ids(tweets, event_name, n)
