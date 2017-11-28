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
from tqdm import tqdm

import settings
from db import events
from db.engines import engine_lmartine as engine
from db.models_new import EventGroup, Tweet
from evaluation.automatic_evaluation import remove_and_stemming


def clean_tweet(tweet):
    return ' '.join(remove_and_stemming(re.sub(r"@\w+", '', re.sub(r"http\S+", '', tweet.text.replace('#', ''))), True))


def filter_tweet(text):
    if text.count('#') > 2:
        return False
    elif text.count('http') > 2:
        return False
    elif text.count('@') > 2:
        return False
    return True


def clustering(n_clusters, tweets):
    tweets = [tweet for tweet in tweets if filter_tweet(tweet.text)]
    clean_tweets = [clean_tweet(tweet) for tweet in tweets]
    vectorizer = TfidfVectorizer()
    tfidf = vectorizer.fit_transform(clean_tweets)
    km = KMeans(n_clusters=n_clusters)
    labels = km.fit_predict(tfidf)

    print("Top terms per cluster:")
    order_centroids = km.cluster_centers_.argsort()[:, ::-1]
    terms = vectorizer.get_feature_names()

    top_terms = top_terms_clusters(n_clusters, order_centroids, terms)

    tweets_labels = [(label, tweet.text) for tweet, label in zip(tweets, labels)]
    return tweets_labels, top_terms


def top_terms_clusters(n_clusters, order_centroids, terms):
    path_top_clusters = Path(settings.LOCAL_DATA_DIR_2, 'data', event_name, 'phrase_reinforcement', str(n_clusters))
    top_terms = defaultdict(list)
    if not path_top_clusters.exists():
        path_top_clusters.mkdir()
    with Path(path_top_clusters, f'top_terms_{n_clusters}.txt').open('w') as terms_file:
        for i in range(n_clusters):
            terms_file.write(f'Cluster {i} \n')
            for ind in order_centroids[i, :10]:
                top_terms[i].append(terms[ind])
                terms_file.write(terms[ind] + '\n')

    return top_terms


def create_json_topic(n_clusters, tweets):
    tweets_labels, top_terms = clustering(n_clusters, tweets)
    tweet_dict = defaultdict(list)

    for label, text in tweets_labels:
        tweet_dict[str(label)].append(text)

    for k, v in tweet_dict.items():
        topic = top_terms[int(k)]
        aux_dict = {'topic': topic[0], 'tweets': v}
        with open(event_name + '_' + str(n_clusters) + '.txt', 'a') as file:
            json.dump(aux_dict, file)
            file.write('\n')


def save_summary(event, n_cluster, tweets):
    path_summary = Path(settings.LOCAL_DATA_DIR_2, 'data', event, 'summaries', 'system', 'ids',
                        f'phrase_reinforcement_{n_cluster}.txt')
    path_json = Path(settings.LOCAL_DATA_DIR_2, 'data', event, 'phrase_reinforcement', str(n_cluster), 'rawData.json')
    with path_json.open('r') as json_file, path_summary.open('w') as summary_file:
        phrase_json = json.load(json_file)
        for k, v in phrase_json.items():
            if 'autoSummary' in v.keys():
                summary = v['autoSummary']
                if summary[len(summary) - 1] == '\n':
                    summary = summary[:len(summary)]
                tweets_text = [tweet.text for tweet in tweets]
                try:
                    tweet = tweets[tweets_text.index(summary)]
                except:
                    tweet = session.query(Tweet).filter(Tweet.text.like(f'%{summary}%')).first()

                summary_file.write(str(tweet.tweet_id) + '\n')


def phrase_reinforcement(n_cluster, tweets):
    if not Path(event_name + '_' + str(n_cluster) + '.txt').exists():
        create_json_topic(n_cluster, tweets)

    path_summaries = Path(settings.LOCAL_DATA_DIR_2, 'data', event_name, 'phrase_reinforcement', str(n_cluster))
    if not path_summaries.exists():
        path_summaries.mkdir()

    if not Path(settings.LOCAL_DATA_DIR_2, 'data', event_name, 'phrase_reinforcement', str(n_cluster),
                'rawData.json').exists():
        subprocess.call(
            ['java', '-jar', 'TwitterSummaryData.jar', event_name + '_' + str(n_cluster) + '.txt',
             path_summaries.__str__() + "/"])

    save_summary(event_name, n_cluster, tweets)


if __name__ == '__main__':
    Session = sessionmaker(engine, autocommit=True)
    session = Session()

    events_names = ['oscar_pistorius', 'nepal_earthquake', 'hurricane_irma2']
    for event_name in events_names:
        print(event_name)
        event = session.query(EventGroup).filter(EventGroup.name == event_name).first()
        event_ids = list(map(int, event.event_ids.split(',')))
        tweets = events.get_tweets(event_name, event_ids, session)
        if event_name == 'libya_hotel':
            n_cluster = [10, 15, 20, 25]
        else:
            n_cluster = [15, 20, 25, 30]
        for n in tqdm(n_cluster):
            phrase_reinforcement(n, tweets)
