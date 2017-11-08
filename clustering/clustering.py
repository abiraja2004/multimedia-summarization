import json
import logging
import sys

import itertools
from sklearn.cluster import AgglomerativeClustering, KMeans
from clustering_online import OnlineClustering
from sqlalchemy.orm import sessionmaker
from tqdm import tqdm

from db.engines import engine_of215 as engine
from db import events
from db.models_new import Document, Cluster, DocumentCluster

from document_representation.get_vectors import *

logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s | %(name)s | %(levelname)s : %(message)s', level=logging.INFO)

Session = sessionmaker(engine, autocommit=True)
session = Session()

# user vars
event_name = sys.argv[1]
algo = sys.argv[2]
rep = sys.argv[3]

event_id = events.get_eventgroup_id(event_name, session)

if rep == "fasttext":
    input_vectors, documents = get_fasttext_vectors(event_name, session)
    rep_params = {}
elif rep == "tfidf":
    input_vectors, tfidf, documents = get_tfidf_vectors(event_name, session)
    rep_params = tfidf.get_params()
    # TODO pop
    # rep_params[""]
elif rep == 'discourse':
    fname = sys.argv[4]
    idx_name = sys.argv[5]
    input_vectors, documents = get_discourse_vectors(event_name, fname, idx_name, session)

    a = float('.'.join(fname.split('_')[-1].split('.')[0:2]))
    rep_params = {"a": a}
else:
    sys.exit(1)

affinities = ('cosine', )
linkages = ('complete', 'average')
n_clusterss = (5, 10, 20, 30)
tau = 0.9

methods = list()

if algo == "agglomerative":
    # agglomerative
    for affinity, linkage, n_clusters in itertools.product(affinities, linkages, n_clusterss):
        agg = AgglomerativeClustering(n_clusters=n_clusters,
                                      affinity=affinity,
                                      linkage=linkage)
        params = agg.get_params()
        params.pop('memory')
        params.pop('pooling_func')
        info = {'name': 'Agglomerative Clustering',
                "rep": rep,
                "rep_params": rep_params,
                'params': params}

        methods.append((agg, info))
elif algo == "kmeans" or algo == "k-means":
    # k-means
    for n_clusters in n_clusterss:
        km = KMeans(n_clusters=n_clusters, n_jobs=-1, max_iter=1000, n_init=100)
        params = km.get_params()
        info = {'name': 'K-Means',
                "rep": rep,
                "rep_params": rep_params,
                'params': params}
        methods.append((km, info))

elif algo == "online":
    # online
    oc = OnlineClustering(tau=tau)
    info = {'name': "Online",
            "rep": rep,
            "rep_params": rep_params,
            "params": {"tau": tau}}

    methods.append((oc, info))

else:
    sys.exit(1)


for method, method_info in tqdm(methods):
    logger.info(f"Method: {method_info['name']}")
    with session.begin():
        cluster = Cluster(json=json.dumps(method_info), eventgroup_id=event_id)
        session.add(cluster)

    method.fit(input_vectors)

    with session.begin():
        for doc, label in zip(documents, method.labels_):
            doc_cluster = DocumentCluster(document_id=doc.id,
                                          cluster_id=cluster.id,
                                          label=label)
            session.add(doc_cluster)
    logger.info("Done.")
