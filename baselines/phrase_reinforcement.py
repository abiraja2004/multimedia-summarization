"""

"""
import json
import subprocess
from collections import defaultdict
from pathlib import Path

from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sqlalchemy.orm import sessionmaker

import settings
from db import datasets, events
from db.engines import engine_lmartine as engine
from evaluation.automatic_evaluation import remove_and_steam

event_name = 'libya_hotel'
event_ids = datasets.libya_hotel

Session = sessionmaker(engine, autocommit=True)
session = Session()


def clustering(n_clusters):
    tweets = events.get_tweets(event_name, event_ids)
    clean_tweets = [remove_and_steam(tweet.text, True) for tweet in tweets]
    vectorizer = TfidfVectorizer()
    tfidf = vectorizer.fit_transform(clean_tweets)
    km = KMeans(n_clusters=n_clusters)
    labels = km.fit_predict(tfidf)
    tweets_labels = [(label, tweet.text) for tweet, label in zip(tweets, labels)]
    return tweets_labels


def create_json_topic(n_clusters):
    tweets_labels = clustering(n_clusters)
    tweet_dict = defaultdict(list)
    data = []
    for label, text in tweets_labels:
        tweet_dict[str(label)].append(text)
    for k, v in tweet_dict.items():
        aux_dict = {'topic': k, 'tweets': v}
        with open(event_name + '.txt', 'a') as file:
            json.dump(aux_dict, file)
            file.write('\n')


def save_summary(event):
    path_summary = Path(settings.LOCAL_DATA_DIR_2, 'data', event, 'summaries', 'system',
                        'phrase_reinforcement_summary.txt')
    path_json = Path(settings.LOCAL_DATA_DIR_2, 'data', event, 'phrase_reinforcement', 'rawData.json')
    with path_json.open('r') as json_file, path_summary.open('w') as summary_file:
        phrase_json = json.load(json_file)
        for k, v in phrase_json.items():
            if 'autoSummary' in v.keys():
                summary = v['autoSummary']
                summary_file.write(summary + '\n')


def phrase_reinforcement(n_cluster):
    if not Path(event_name + '.txt').exists():
        create_json_topic(n_cluster)

    path_summaries = Path(settings.LOCAL_DATA_DIR_2, 'data', event_name, 'phrase_reinforcement').__str__() + '/'
    print(path_summaries)
    subprocess.call(['java', '-jar', 'TwitterSummaryData.jar', event_name + '.txt', path_summaries])
    save_summary(event_name)

phrase_reinforcement(10)

