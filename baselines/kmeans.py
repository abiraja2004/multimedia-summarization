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


def filter_tweet(text):
    if text.count('#') > 2:
        return False
    elif text.count('http') > 2:
        return False
    elif text.count('@') > 2:
        return False
    return True


def clustering(n_clusters, event_name, event_ids, session):
    tweets = get_tweets(event_name, event_ids, session)
    tweets = [tweet for tweet in tweets if filter_tweet(tweet.text)]
    clean_tweets = [(tweet.text, clean_tweet(tweet)) for tweet in tweets]
    vectorizer = TfidfVectorizer()
    tfidf = vectorizer.fit_transform([clean[1] for clean in clean_tweets])
    km = KMeans(n_clusters=n_clusters)
    km.fit(tfidf)

    print("Top terms per cluster:")
    order_centroids = km.cluster_centers_.argsort()[:, ::-1]
    terms = vectorizer.get_feature_names()

    path_top_clusters = Path(settings.LOCAL_DATA_DIR_2, 'data', event_name, 'kmeans_centroid')

    if not path_top_clusters.exists():
        path_top_clusters.mkdir()

    with Path(path_top_clusters, f'top_terms_{n_clusters}.txt').open('w') as terms_file:
        for i in range(n_clusters):
            print("Cluster %d:" % i),
            terms_file.write(f'Cluster {i}')
            for ind in order_centroids[i, :10]:
                print(' %s' % terms[ind])
                terms_file.write(terms[ind] + '\n')

    closest, _ = pairwise_distances_argmin_min(km.cluster_centers_, tfidf, metric='cosine')
    tokens_closest = []
    tweet_closest = []
    for close_index in closest:
        tokens_closest.append(vectorizer.inverse_transform(tfidf[close_index]))
        tweet_closest.append(tweets[close_index])
    return tweet_closest


def save_ids(tweets, event_name, n_clusters):
    with Path(settings.LOCAL_DATA_DIR_2, 'data', event_name, 'summaries', 'system', 'ids',
              f'kmeans_centroid_{n_clusters}.txt').open('w') as summary:
        tweet_ids = [str(tweet.tweet_id) + '\n' for tweet in tweets]
        summary.writelines(tweet_ids)

if __name__ == '__main__':

    Session = sessionmaker(engine, autocommit=True)
    session = Session()

    events_names = ['oscar_pistorius', 'nepal_earthquake', 'hurricane_irma2']
    for event_name in events_names:
        event = session.query(EventGroup).filter(EventGroup.name == event_name).first()
        ids = list(map(int, event.event_ids.split(',')))

        n_cluster = [15, 20, 25, 30]
        for n in n_cluster:
            tweets = clustering(n, event_name, ids, session)
            save_ids(tweets, event_name, n)
