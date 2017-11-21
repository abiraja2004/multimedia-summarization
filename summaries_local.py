"""
Para correr desde el "server"
"""

import json
import logging
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from sqlalchemy.orm import sessionmaker
from tqdm import tqdm

from db import events
from db.engines import engine_lmartine as engine
from db.models_new import Document, Cluster, DocumentCluster
from ranking.ranking_cluster_timeimpact import rank_clusters

logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s | %(name)s | %(levelname)s : %(message)s', level=logging.INFO)

number_summaries = 5


Session = sessionmaker(engine, autocommit=True)
session = Session()

event_name = 'hurricane_irma2'
event_id = events.get_eventgroup_id(event_name, session)

results_dir = Path('results', event_name)
if not results_dir.exists():
    results_dir.mkdir()


def name(params):
    tech = "-".join(params["name"].split())
    n_clusters = params['params']['n_clusters']
    rep = params["rep"]

    fname = f'cl_{tech}_{rep}_nclusters_{n_clusters}.html'

    return Path(fname)

clusters = session.query(Cluster).filter(Cluster.eventgroup_id == event_id).all()

for i, cluster in tqdm(enumerate(clusters), total=len(clusters)):
    env = Environment(loader=FileSystemLoader('results'), trim_blocks=True)

    document_cluster = session.query(Document, DocumentCluster) \
        .join(DocumentCluster, DocumentCluster.document_id == Document.id) \
        .filter(DocumentCluster.cluster_id == cluster.id).all()

    params = json.loads(cluster.json)
    n_clusters = params['params']['n_clusters']
    fname = name(params)

    j_cluster = []
    sort_labels = rank_clusters(cluster.id, session)
    with (results_dir / fname).open('w') as f:
        for j in sort_labels:
            docs_in_cluster_j = [d for d, l in document_cluster if l.label == j]

            if len(docs_in_cluster_j) == 1:
                continue

            docs_in_cluster_j.sort(key=lambda x: x.total_rts, reverse=True)
            j_cluster.append([doc.tweet_id for doc in docs_in_cluster_j[:number_summaries]])

        t = env.get_template('results_template.html').render(params=params,
                                                             json=json.dumps(params),
                                                             clusters=j_cluster)
        f.write(t)

