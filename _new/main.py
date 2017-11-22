from representation import *
from clustering import *
from itertools import product
from tqdm import tqdm
from summary import gen_summary

import db
import models
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s | %(name)s | %(levelname)s : %(message)s', level=logging.INFO)

"""
use_glove = (True, False)
events = (7, 8, 9)
full = (True, False)

reps = (discourse, average_we)
clustering = (agglomerative,)
n_clusterss = (5, 10, 20)

for cl, n_clusters, rep, e, f, g in tqdm(product(clustering, n_clusterss, reps, events, full, use_glove)):
    logger.info(str((cl, n_clusters, rep, e, f, g)))
    vectors, doc_ids, params = rep(eventgroup_id=e, full=f, use_glove=g, overwrite=False)
    cl(eventgroup_id=e, input_vectors=vectors, rep_info=params, n_clusters=n_clusters)
"""

clusters = db.session.query(models.Cluster).all()
for cluster in tqdm(clusters):
    name = db.get_eventgroup_name(cluster.eventgroup_id).name
    logger.info(f"Event: {name}, Cluster: {cluster}")
    gen_summary(name, cluster, db.session)
