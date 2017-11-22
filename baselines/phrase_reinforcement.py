"""

"""
import json
import re
import subprocess
from collections import defaultdict
from pathlib import Path

from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sqlalchemy.orm import sessionmaker

import settings
from db import events
from db.engines import engine_lmartine as engine
from db.models_new import EventGroup, Tweet
from evaluation.automatic_evaluation import remove_and_steam


def clean_tweet(tweet):
    return ' '.join(remove_and_steam(re.sub(r"@\w+", '', re.sub(r"http\S+", '', tweet.text.replace('#', ''))), True))


def filter_tweet(text):
    if text.count('#') > 2:
        return False
    elif text.count('http') > 2:
        return False
    elif text.count('@') > 2:
        return False
    return True


def clustering(n_clusters):
    tweets = events.get_tweets(event_name, event_ids, session)
    tweets = [tweet for tweet in tweets if filter_tweet(tweet.text)]
    clean_tweets = [clean_tweet(tweet) for tweet in tweets]
    vectorizer = TfidfVectorizer()
    tfidf = vectorizer.fit_transform(clean_tweets)
    km = KMeans(n_clusters=n_clusters)
    labels = km.fit_predict(tfidf)

    print("Top terms per cluster:")
    order_centroids = km.cluster_centers_.argsort()[:, ::-1]
    terms = vectorizer.get_feature_names()

    path_top_clusters = Path(settings.LOCAL_DATA_DIR_2, 'data', event_name, 'phrase_reinforcement', n_clusters)

    if not path_top_clusters.exists():
        path_top_clusters.mkdir()

    with Path(path_top_clusters, f'top_terms_{n_clusters}.txt').open('w') as terms_file:
        for i in range(n_clusters):
            print("Cluster %d:" % i),
            terms_file.write(f'Cluster {i}')
            for ind in order_centroids[i, :10]:
                print(' %s' % terms[ind])
                terms_file.write(terms[ind] + '\n')

    tweets_labels = [(label, tweet.text) for tweet, label in zip(tweets, labels)]
    return tweets_labels


def create_json_topic(n_clusters):
    tweets_labels = clustering(n_clusters)
    tweet_dict = defaultdict(list)

    for label, text in tweets_labels:
        tweet_dict[str(label)].append(text)

    for k, v in tweet_dict.items():
        aux_dict = {'topic': k, 'tweets': v}
        with open(event_name + '_' + str(n_clusters) + '.txt', 'a') as file:
            json.dump(aux_dict, file)
            file.write('\n')


def save_summary(event, n_cluster):
    path_summary = Path(settings.LOCAL_DATA_DIR_2, 'data', event, 'summaries', 'system', 'ids'
                        f'phrase_reinforcement_{n_cluster}.txt')
    path_json = Path(settings.LOCAL_DATA_DIR_2, 'data', event, 'phrase_reinforcement', 'rawData.json')
    with path_json.open('r') as json_file, path_summary.open('w') as summary_file:
        phrase_json = json.load(json_file)
        for k, v in phrase_json.items():
            if 'autoSummary' in v.keys():
                summary = v['autoSummary']
                summary = summary.replace('\n', '')
                tweet = session.query(Tweet).filter(Tweet.text.like(f'%{summary}%')).first()
                summary_file.write(tweet.tweet_id + '\n')


def phrase_reinforcement(n_cluster):
    if not Path(event_name + '_' + str(n_cluster) + '.txt').exists():
        create_json_topic(n_cluster)

    path_summaries = Path(settings.LOCAL_DATA_DIR_2, 'data', event_name, 'phrase_reinforcement', n_cluster)
    if not path_summaries.exists():
        path_summaries.mkdir()

    subprocess.call(
        ['java', '-jar', 'TwitterSummaryData.jar', event_name + '_' + str(n_cluster) + '.txt',
         path_summaries.__str__() + "/"])
    save_summary(event_name, n_cluster)


if __name__ == '__main__':
    Session = sessionmaker(engine, autocommit=True)
    session = Session()

    events_names = ['oscar_pistorius', 'nepal_earthquake', 'hurricane_irma2']
    for event_name in events_names:
        event = session.query(EventGroup).filter(EventGroup.name == event_name).first()
        event_ids = list(map(int, event.event_ids.split(',')))

        n_cluster = [15, 20, 25, 30]
        for n in n_cluster:
            phrase_reinforcement(n)
