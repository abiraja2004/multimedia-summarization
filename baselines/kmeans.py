import re

from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import pairwise_distances_argmin_min
from sqlalchemy.orm import sessionmaker

from db import datasets, events
from db.engines import engine_lmartine as engine
from evaluation.automatic_evaluation import remove_and_steam


def clean_tweet(tweet):
    return ' '.join(remove_and_steam(re.sub(r"@\w+", '', re.sub(r"http\S+", '', tweet.text.replace('#', '')))))


def clustering(n_clusters, event_name, event_ids, session):
    tweets_ids = events.get_tweet_ids(event_name, event_ids, session)
    tweets = events.get_tweets_from_ids(tweets_ids, session)
    clean_tweets = [(tweet.text, clean_tweet(tweet.text, True)) for tweet in tweets]
    vectorizer = TfidfVectorizer()
    tfidf = vectorizer.fit_transform([clean_tweet[1] for clean_tweet in clean_tweets])
    km = KMeans(n_clusters=n_clusters)

    closest, _ = pairwise_distances_argmin_min(km.cluster_centers_, tfidf)
    tokens_closest = []
    tweet_closest = []
    for close_index in closest:
        tokens_closest.append(vectorizer.inverse_transform(tfidf[close_index]))
        tweet_closest.append(tweets[close_index])
    print(tweet_closest)
    return tweet_closest


if __name__ == '__main__':
    event = 'irma'
    ids = datasets.irma

    Session = sessionmaker(engine, autocommit=True)
    session = Session()
    tweets = clustering(10, event, ids, session)
