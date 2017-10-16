from db.engines import connect_from_rafike
from db.models_new import *
from sqlalchemy.orm import sessionmaker
import logging

import spacy
import settings
from operator import itemgetter
from collections import defaultdict
from tqdm import tqdm
import time
import re

import theano.tensor as T
import theano
import numpy as np

logging.basicConfig(format='%(asctime)s | %(name)s | %(levelname)s : %(message)s', level=logging.INFO)

event_name = "hurricane_irma"
doc_vectors = np.load(f'fasttext_vectors_event_{event_name}.npy')


def cos_sim_():
    docv = T.dmatrix('docv')
    clusters = T.dmatrix('clusters')
    z = T.mean(T.dot(docv / T.sqrt(T.sum(T.pow(docv, 2))),
                     clusters / T.sqrt(T.sum(T.pow(clusters, 2), axis=0))))

    # z = T.mean(T.dot(docv, clusters))
    return theano.function([docv, clusters], z)


# x = np.array([1, 2, 3])[None]
# y = np.array([[1, 12, 7], [2, 4 , 1], [3, 6, 4]])

def mean_():
    m = T.dmatrix('vectors')
    z = T.mean(m, axis=0)
    return theano.function([m], z)


similarity = cos_sim_()
mean = mean_()
threshold = 0.9
clusters = []
clusters_idx = []

for i, vector in tqdm(enumerate(doc_vectors), total=len(doc_vectors)):
    if np.isnan(vector).any():
        continue
    j_max, sim_max, vector_max = -1, -1, None
    for j, cluster in enumerate(clusters):
        sim = similarity(vector, cluster)
        if sim > threshold and sim > sim_max:
            j_max = j
            sim_max = sim
            vector_max = vector

    if j_max > -1:
        clusters[j_max] = np.concatenate([clusters[j_max], vector_max.T], axis=1)
        clusters_idx[j_max].append(i)
    else:
        clusters.append(vector.T)
        clusters_idx.append([i])


# with open("irma_ids.txt", 'w') as f:
#     for idx, cluster in enumerate(sorted(clusters_idx, key=lambda x: len(x), reverse=True)):
#         if len(cluster) == 1:
#             continue
#         # print("cluster:", idx, "-", "size:", len(cluster))
#
#         cluster_docs = sorted([documents[i] for i in cluster], key=lambda x: x.total_rts + x.total_favs, reverse=True)
#         # docs = sorted(cluster_docs, key=itemgetter(2), reverse=True)[:5]
#         for d in cluster_docs[:1]:
#             f.write(str(d.tweet_id) + '\n')
#         # print()
#         # print()
#         # input()
