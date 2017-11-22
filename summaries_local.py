"""
Para correr desde el "server"
"""

import json
import logging
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from tqdm import tqdm

from db.models_new import Document, DocumentCluster, Tweet
from ranking.ranking_cluster_timeimpact import rank_clusters

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

    params = json.loads(cluster.json)
    fname = f"{event_name}_{cluster.id}.html"

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
