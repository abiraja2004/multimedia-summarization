import json
import logging
import numpy as np
from pathlib import Path, PosixPath
from scipy.sparse.csr import csr_matrix
from operator import itemgetter

from jinja2 import Environment, FileSystemLoader
from tqdm import tqdm

from models import Document, DocumentCluster, Tweet
from ranking import rank_clusters

from sklearn.cluster import KMeans, AgglomerativeClustering
from sklearn.neighbors import NearestNeighbors
from sklearn.externals import joblib


logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s | %(name)s | %(levelname)s : %(message)s', level=logging.INFO)


def jaccard(t1: set, t2: set):
    return len(t1 & t2) / len(t1 | t2)


def gen_summary(event_name, cluster, session, sim_threshold=0.5):
    results_dir = Path('results', event_name)
    if not results_dir.exists():
        results_dir.mkdir()

    tweets_per_cluster = 5
    env = Environment(loader=FileSystemLoader('results'), trim_blocks=True)

    document_cluster = session.query(Document, DocumentCluster, Tweet) \
        .join(DocumentCluster, DocumentCluster.document_id == Document.id) \
        .join(Tweet, Tweet.tweet_id == Document.tweet_id) \
        .filter(DocumentCluster.cluster_id == cluster.id).all()

    params = eval(cluster.json)
    rep = params['repr']
    n_clusters = params['n_clusters']
    cluster_algo = params['clustering'].lower()
    fname = f"{cluster.id}_{cluster_algo}_{n_clusters}_{rep}.html"

    j_cluster = []
    sort_labels = rank_clusters(cluster.id, session)
    with (results_dir / fname).open('w') as f:

        for j in tqdm(sort_labels):
            docs_in_cluster_j = [(doc, tweet) for doc, doc_cluster, tweet in document_cluster if doc_cluster.label == j]

            if len(docs_in_cluster_j) == 1:
                continue

            sorted_docs = sorted(docs_in_cluster_j, key=lambda x: x[0].total_rts, reverse=True)

            t0 = set(map(lambda x: x.lower(), sorted_docs[0][1].text))
            selected_tweets = [t0]
            selected_ids = [sorted_docs[0][1].tweet_id]

            for _, tweet in sorted_docs[1:]:
                t1 = set(map(lambda s: s.lower(), tweet.text.split()))
                id1 = tweet.tweet_id

                if any(jaccard(t1, t2) > sim_threshold for t2 in selected_tweets):
                    continue
                else:
                    selected_ids.append(id1)

                if len(selected_ids) == tweets_per_cluster:
                    break

            j_cluster.append(selected_ids)

        t = env.get_template('results_template.html').render(params=params,
                                                             json=json.dumps(params),
                                                             clusters=j_cluster,
                                                             labels=sort_labels)
        f.write(t)


def gen_summary2(event_name, cluster_fname, repr_fname, session):
    results_dir = Path('results', event_name)
    if not results_dir.exists():
        results_dir.mkdir()

    tweets_per_cluster = 1
    env = Environment(loader=FileSystemLoader('results'), trim_blocks=True)

    input_vectors, doc_ids, repr_info = joblib.load(repr_fname)
    model, cluster_info = joblib.load(cluster_fname)
    doc_ids = np.array(doc_ids)

    rep = cluster_info['repr']
    n_clusters = cluster_info['n_clusters']
    cluster_algo = cluster_info['clustering'].lower()
    cluster_id = cluster_info['cluster_id']

    fname = f"{cluster_id}_{cluster_algo}_{n_clusters}_{rep}.html"

    j_cluster = []
    sorted_labels = rank_clusters(cluster_id, session)

    with (results_dir / fname).open('w') as f:
        if isinstance(model, AgglomerativeClustering):
            if isinstance(input_vectors, csr_matrix):
                input_vectors = input_vectors.todense()
                centroids = []
                for label in range(min(model.labels_), max(model.labels_) + 1):
                    centroids.append(np.array(input_vectors[model.labels_ == label].mean(0))[0].T)
            else:
                centroids = []
                for label in range(min(model.labels_), max(model.labels_) + 1):
                    centroids.append(input_vectors[model.labels_ == label].mean(0))
        else:
            centroids = model.cluster_centers_

        knn = NearestNeighbors(n_neighbors=tweets_per_cluster, n_jobs=-1)
        knn.fit(input_vectors)
        _, doc_indices = knn.kneighbors(centroids)
        sorted_docs_indices = doc_indices[sorted_labels]

        for doc_indices in sorted_docs_indices:
            documents = session.query(Document.tweet_id).filter(Document.id.in_(doc_ids[doc_indices])).all()
            j_cluster.append(list(map(itemgetter(0), documents)))

        cluster_info['fname'] = cluster_info['fname'].as_posix()
        cluster_info['label_dist'] = {int(k): int(v) for k, v in cluster_info['label_dist'].items()}

        t = env.get_template('results_template.html').render(params=cluster_info,
                                                             json=json.dumps(cluster_info),
                                                             clusters=j_cluster,
                                                             event_name=event_name,
                                                             labels=sorted_labels)
        f.write(t)
