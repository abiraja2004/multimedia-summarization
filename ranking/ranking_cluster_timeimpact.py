# For a specific cluster calculate the distribution of time intervals beteween the tweets
# 54,25
from collections import defaultdict

import numpy as np

from db.clusters import get_documents_cluster
from db.models_new import Tweet, DocumentTweet


def return_intersection(hist_1, hist_2):
    minima = np.minimum(hist_1, hist_2)
    intersection = np.true_divide(np.sum(minima), np.sum(hist_2))
    return intersection


# Calculate the score of a histogram as the linear combination of the bins
def linear_combination(histogram):
    return 0.4 * histogram[0] + 0.3 * histogram[1] + 0.175 * histogram[2] + 0.125 * histogram[3]


# Calculate the histogram of time frecuency
def calculate_time_histogram(clustering, topic, session):
    docs = get_documents_cluster(clustering, session)
    topic_dict = defaultdict(list)

    for doc in docs:
        topic_dict[doc[0]].append(doc[1])
    specific_topic = topic_dict[topic]
    docs_id = [doc.id for doc in specific_topic]
    tweets = session.query(DocumentTweet.tweet_id).filter(DocumentTweet.document_id.in_(docs_id)).all()

    tweets = [x[0] for x in tweets]
    dates = session.query(Tweet.created_at).filter(Tweet.tweet_id.in_(tweets)).all()

    differences = []
    dates.sort(key=lambda x: x[0], reverse=True)

    for i in range(len(dates) - 1):
        minutes_diff = dates[i][0] - dates[i + 1][0]
        differences.append(round(minutes_diff.total_seconds(), -1))
    differences.sort()
    histogram, bins = np.histogram(differences, bins=45, range=(0, 1080))

    return histogram


def rank(histograms, score=True):
    ranking = []
    for cluster, histogram in histograms.items():
        ranking.append((cluster, histogram[0]))

    ranking.sort(key=lambda x: x[1], reverse=True)
    ranking.append((-1, 0))
    if score:
        ranking = [x[0] for x in ranking]
    return ranking


from db.models_new import Cluster, DocumentCluster, Document, Tweet, DocumentTweet
import json

def gen_histograms(clustering_id, session):
    # TODO implementar con la BD completa
    clustering = session.query(Cluster).filter(Cluster.id == clustering_id).first()

    doc_info = session.query(Document, DocumentCluster, Tweet) \
        .join(DocumentCluster, DocumentCluster.document_id == Document.id) \
        .join(Tweet, Tweet.tweet_id == Document.tweet_id) \
        .filter(DocumentCluster.cluster_id == clustering_id).all()

    params = json.loads(clustering.params)
    n_clusters = params['n_clusters']

    # TODO considerar todos los tweets de un documento para el calculo de histograma
    for i in range(n_clusters):
        documents = [doc for doc, label_info, tweet in doc_info if label_info.label == i]
