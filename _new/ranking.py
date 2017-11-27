# For a specific cluster calculate the distribution of time intervals beteween the tweets
# 54,25

from collections import OrderedDict

from pathlib import PosixPath

import numpy as np
from tqdm import tqdm, trange

from models import Cluster, DocumentCluster, Document, Tweet


def rank_clusters(clustering_id, session):
    clustering = session.query(Cluster).filter(Cluster.id == clustering_id).first()
    params = eval(clustering.json)
    n_clusters = params['n_clusters']

    times_per_cluster = OrderedDict()
    for label in trange(n_clusters):
        doc_cluster = session.query(DocumentCluster, Document, Tweet) \
            .join(Document, Document.id == DocumentCluster.document_id) \
            .join(Tweet, Tweet.tweet_id == Document.tweet_id) \
            .filter(DocumentCluster.cluster_id == clustering_id) \
            .filter(DocumentCluster.label == label) \
            .all()

        times = []
        for _, doc, tweet in tqdm(doc_cluster):
            times.append(tweet.created_at)
        times_per_cluster[label] = sorted(times)

    time_differences = OrderedDict()
    histograms = OrderedDict()

    for label, times in tqdm(times_per_cluster.items(), desc="time diff"):
        diffs = []

        t0 = times[0]
        for t in times[1:]:
            delta = (t - t0).total_seconds()
            diffs.append(delta)
            t0 = t

        time_differences[label] = diffs
        histogram, _ = np.histogram(diffs, bins=45, range=(0, 1080), density=False)
        histograms[label] = histogram

    first_bins = [h[0] for h in histograms.values()]
    labels_ranked = np.argsort(first_bins)[::-1]

    return labels_ranked
