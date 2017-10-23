import itertools
import json
import logging
import sys

import numpy as np
from sklearn.cluster import AgglomerativeClustering, KMeans
from sqlalchemy.orm import sessionmaker
from tqdm import tqdm

from db.engines import engine_of215 as engine
from db.models_new import Document, Cluster, DocumentCluster

event_name = sys.argv[1]

logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s | %(name)s | %(levelname)s : %(message)s', level=logging.INFO)
# tokenizer = Tokenizer()

# server, engine = connect_from_rafike(username='mquezada', password='100486')
Session = sessionmaker(engine, autocommit=True)
session = Session()

# documents = events.get_documents_from_event(event_name, session)
documents = session.query(Document).all()
doc_vectors = np.load(f'data/fasttext_vectors_event_{event_name}.npy')

# all indices
idx = range(len(doc_vectors))
# indices de doc_vectors con NA (son como 15 no más :P)
remove_idx = np.where(np.isnan(doc_vectors).any(axis=1))[0]

input_vectors = [doc_vectors[i] for i in idx if i not in remove_idx]
documents = np.array([documents[i] for i in idx if i not in remove_idx])

affinities = ('cosine', )
linkages = ('complete', 'average')
n_clusterss = (5, 10, 20, 30)

methods = list()

# agglomerative
for affinity, linkage, n_clusters in itertools.product(affinities, linkages, n_clusterss):
    agg = AgglomerativeClustering(n_clusters=n_clusters,
                                  affinity=affinity,
                                  linkage=linkage)
    params = agg.get_params()
    params.pop('memory')
    params.pop('pooling_func')
    info = {'name': 'Agglomerative Clustering', 'params': params}

    methods.append((agg, info))

# k-means
for n_clusters in n_clusterss:
    km = KMeans(n_clusters=n_clusters, n_jobs=-1, max_iter=1000, n_init=100)
    params = km.get_params()
    info = {'name': 'K-Means', 'params': params}

    methods.append((km, info))

for method, method_info in tqdm(methods):
    # logger.info(f"Method: {method_info['name']}")
    with session.begin():
        cluster = Cluster(json=json.dumps(method_info))
        session.add(cluster)

    method.fit(input_vectors)
    with session.begin():
        for doc, label in zip(documents, method.labels_):
            doc_cluster = DocumentCluster(document_id=doc.id,
                                          cluster_id=cluster.id,
                                          label=label)
            session.add(doc_cluster)
    logger.info("Done.")