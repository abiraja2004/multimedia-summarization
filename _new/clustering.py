from sklearn.cluster import KMeans, AgglomerativeClustering
from tqdm import tqdm
from pathlib import Path
import db
import logging
from sklearn.externals import joblib
from collections import Counter


def save_cluster(eventgroup_id, info, model, doc_ids, fname):
    with db.session.begin():
        cluster = db.Cluster(eventgroup_id=eventgroup_id,
                             json=info)
        db.session.add(cluster)

    with db.session.begin():
        for doc_id, label in tqdm(list(zip(doc_ids, model.labels_)), desc="saving cluster"):
            cluster_doc = db.DocumentCluster(document_id=doc_id,
                                             cluster_id=cluster.id,
                                             label=label)
            db.session.add(cluster_doc)

    joblib.dump((model, info, cluster), fname)
    return model, info, cluster


def kmeans(eventgroup_id,
           repr_fname,
           n_clusters,
           overwrite=False,
           other_params=None):

    input_vectors, doc_ids, rep_info = joblib.load(repr_fname)

    #rep = '_'.join(f'{k}-{v}' for k, v in rep_info.items())
    fname = f'data/clusters/{eventgroup_id}_clustering_kmeans_{n_clusters}_{rep_info["name"]}.pkl'
    path = Path(fname)

    if path.exists() and not overwrite:
        logging.info(f"file {path.as_posix()} exists")
        return joblib.load(path)

    km = KMeans(n_clusters=n_clusters)
    km.fit_transform(input_vectors)

    info = {
        'clustering': 'K-Means',
        'repr': rep_info['name'],
        'event': eventgroup_id,
        'n_clusters': n_clusters,
        'label_dist': dict(Counter(km.labels_)),
        'repr_params': rep_info,
        'clustering_params': km.get_params()
    }

    return save_cluster(eventgroup_id, info, km, doc_ids, fname)


def agglomerative(eventgroup_id,
                  repr_fname,
                  n_clusters,
                  overwrite=False,
                  other_params=None):

    input_vectors, doc_ids, rep_info = joblib.load(repr_fname)

    # rep = '_'.join(f'{k}-{v}' for k, v in rep_info.items())
    # ot = '_'.join(f'{k}-{v}' for k, v in other_params.items())
    fname = f'data/clusters/{eventgroup_id}_clustering_agglomerative_{n_clusters}_{rep_info["name"]}.pkl'
    path = Path(fname)

    if path.exists() and not overwrite:
        logging.info(f"file {path.as_posix()} exists")
        return joblib.load(path)

    linkage = other_params['linkage']
    affinity = other_params['affinity']

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
        'label_dist': dict(Counter(ac.labels_)),
        'repr_params': rep_info,
        'clustering_params': ac_params
    }

    return save_cluster(eventgroup_id, info, ac, doc_ids, fname)
