from sklearn.cluster import KMeans, AgglomerativeClustering
from itertools import product
from tqdm import tqdm
from pathlib import Path
import db
import logging
from sklearn.externals import joblib


def kmeans(eventgroup_id, input_vectors, rep_info, n_clusters, overwrite=False):
    fname = f'data/{eventgroup_id}_clustering_kmeans_{n_clusters}.pkl'
    #path = Path(fname)

    #if path.exists() and not overwrite:
    #    logging.info(f"file {path.as_posix()} exists")
    #    return joblib.load(path)

    docs = db.get_documents(eventgroup_id, full=True)
    km = KMeans(n_clusters=n_clusters)
    km.fit_transform(input_vectors)

    info = {
        'clustering': 'K-Means',
        'repr': rep_info['name'],
        'event': eventgroup_id,
        'n_clusters': n_clusters,
        'repr_params': rep_info,
        'clustering_params': km.get_params()
    }

    with db.session.begin():
        cluster = db.Cluster(eventgroup_id=eventgroup_id,
                             json=info)
        db.session.add(cluster)

    with db.session.begin():
        for (doc_id, label) in tqdm(list(zip(docs.keys(), km.labels_)), desc="saving cluster"):
            cluster_doc = db.DocumentCluster(document_id=doc_id,
                                             cluster_id=cluster.id,
                                             label=label)
            db.session.add(cluster_doc)

    joblib.dump((km, info), fname)
    return km, info


def agglomerative(eventgroup_id,
                  input_vectors,
                  rep_info,
                  n_clusters,
                  overwrite=False):
    fname = f'data/{eventgroup_id}_clustering_agglomerative_{n_clusters}.pkl'
    # path = Path(fname)

    # if path.exists() and not overwrite:
    #     logging.info(f"file {path.as_posix()} exists")
    #     return joblib.load(path)

    docs = db.get_documents(eventgroup_id, full=True)
    linkages = ('complete', 'average')
    affinity = ('cosine', 'euclidean')

    for linkage, affinity in product(linkages, affinity):
        ac = AgglomerativeClustering(n_clusters=n_clusters, affinity=affinity, linkage=linkage)

        if hasattr(input_vectors, 'todense'):
            ac.fit(input_vectors.todense())
        else:
            ac.fit(input_vectors)

        ac_params = ac.get_params()
        ac_params.pop('memory')
        ac_params.pop('pooling_func')

        info = {
            'clustering': f'Agglomerative-{linkage}-{affinity}',
            'repr': rep_info['name'],
            'event': eventgroup_id,
            'n_clusters': n_clusters,
            'repr_params': rep_info,
            'clustering_params': ac_params
        }

        with db.session.begin():
            cluster = db.Cluster(eventgroup_id=eventgroup_id,
                                 json=info)
            db.session.add(cluster)

        with db.session.begin():
            for (doc_id, label) in tqdm(list(zip(docs.keys(), ac.labels_)), desc="saving cluster"):
                cluster_doc = db.DocumentCluster(document_id=doc_id,
                                                 cluster_id=cluster.id,
                                                 label=label)
                db.session.add(cluster_doc)

        joblib.dump((ac, info), fname)
