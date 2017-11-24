from representation import *
from clustering import *
from itertools import product
from tqdm import tqdm
from summary import gen_summary
from pathlib import Path

import db
import models
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s | %(name)s | %(levelname)s : %(message)s', level=logging.INFO)

glove = (False, True)
events = (7, 8, 9)
overwrite = False
full = (False, True)
reps = (average_we, discourse, tfidf)

combinaciones = list(product(reps, events, full, glove))

for representation, event_id, use_full, use_glove in tqdm(combinaciones):
    print('\n' * 3)
    name = db.get_eventgroup_name(event_id).name
    logger.info(f"representation={representation}, event={name}, "
                f"full={use_full}, glove={use_glove}, overwrite={overwrite}")

    representation(eventgroup_id=event_id,
                   use_full=use_full,
                   use_glove=use_glove,
                   overwrite=overwrite)

methods = (agglomerative,)
affinities = ('cosine', 'euclidean')
linkages = ('complete', 'average')

n_clusterss = (5, 10, 20)

comb = list(product(methods, affinities, linkages)) + [(kmeans, None, None)]
comb = list(product(comb, n_clusterss))

for fname in tqdm(list(Path('data').glob('representation_*'))):
    for (method, affinity, linkage), n_clusters in tqdm(comb):
        event_id = int(fname.as_posix().split('_')[2].split('.')[0])
        name = db.get_eventgroup_name(event_id).name

        params = {'affinity': affinity, 'linkage': linkage}

        logger.info(f"method={method}, n_clusters={n_clusters}, file={fname}, event={event_id}/{name}, params={params}")
        method(event_id, fname, n_clusters, overwrite=overwrite, other_params=params)

        # gen_summary(name, cluster, db.session)
