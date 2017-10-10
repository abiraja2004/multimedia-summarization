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

# load pre-trained vectors
from gensim.models import KeyedVectors

logging.basicConfig(format='%(asctime)s | %(name)s | %(levelname)s : %(message)s', level=logging.INFO)


server, engine = connect_from_rafike(username='mquezada', password='100486')
Session = sessionmaker(engine, autocommit=True)
session = Session()

documents = session.query(Document).all()

nlp = spacy.load('en', parser=False, tagger=False, entity=False)

path = '/home/mquezada/word_embeddings/model.vec'
w2v = KeyedVectors.load_word2vec_format(path)


def gen_vectors(docs):
    vectors = []
    for d in tqdm(docs):
        text = d.text.split()
        v = []
        for token in text:
            try:
                v.append(w2v[token.lower()])
            except KeyError:
                continue
        vectors.append(np.mean(v, axis=0)[None])
    return vectors


def cos_sim_():
    docv = T.dmatrix('docv')
    clusters = T.dmatrix('clusters')
    z = T.mean(T.dot(docv / T.sqrt(T.sum(T.pow(docv, 2))),
                     clusters / T.sqrt(T.sum(T.pow(clusters, 2), axis=0))))
    return theano.function([docv, clusters], z)


# x = np.array([1, 2, 3])[None]
# y = np.array([[1, 12, 7], [2, 4 , 1], [3, 6, 4]])

def mean_():
    m = T.dmatrix('vectors')
    z = T.mean(m, axis=0)
    return theano.function([m], z)


similarity = cos_sim_()
mean = mean_()
vectors = gen_vectors(documents)
threshold = 0.9
clusters = []
clusters_idx = []

for i, vector in tqdm(enumerate(vectors), total=len(vectors)):
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