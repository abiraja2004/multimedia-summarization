from db.models_new import *
from db.engines import engine_of215 as engine
from sqlalchemy.orm import sessionmaker
import logging
from db.events import get_documents_from_event
from sklearn.decomposition import PCA

import spacy
import settings
from operator import itemgetter
from collections import defaultdict
from tqdm import tqdm, trange
import time
import re

import numpy as np
import spacy

# load pre-trained vectors
from gensim.models import KeyedVectors


import sys

event_name = sys.argv[1]
a = float(sys.argv[2])

# event_name = "hurricane_irma2"
# a = .01

logging.basicConfig(format='%(asctime)s | %(name)s | %(levelname)s : %(message)s', level=logging.INFO)
Session = sessionmaker(engine, autocommit=True)
session = Session()

nlp = spacy.load('en', parser=False, tagger=False, entity=False)

documents = get_documents_from_event(event_name, session)

path = '/home/mquezada/phd/multimedia-summarization/data/ft_alltweets_model.vec'
w2v = KeyedVectors.load_word2vec_format(path)

freq_path = '/home/mquezada/phd/multimedia-summarization/data/wordfrequencies_relative.tsv'
freqs = dict()

pca = PCA(n_components=1)

with open(freq_path) as f:
    for line in f:
        word, freq = line.split()
        freqs[word] = float(freq)

doc_stream = nlp.pipe([doc.text for doc in documents[:, 0]], n_threads=16)
vs = np.empty((len(documents), w2v.vector_size))

for i, doc in tqdm(enumerate(doc_stream), total=len(documents), desc="creating vectors"):
    doc_vector = []

    # clean documents to the same WE format
    indexes = [m.span() for m in re.finditer('#\w+', doc.text, flags=re.IGNORECASE)]
    for start, end in indexes:
        doc.merge(start_idx=start, end_idx=end)

    for token in doc:
        if token.pos_ == "PUNCT" or \
                token.is_punct or \
                token.is_space or \
                token.text.startswith('@') or \
                token.like_url:
            continue

        if token.lower_ in w2v:
            w = token.lower_
            vw = w2v[w]
            pw = freqs[w]

            doc_vector.append(a / (a + pw) * vw)

    # representative vector is the average of all words
    vector = np.mean(doc_vector, axis=0)[None]

    vs[i] = vector

# all indices
idx = list(range(len(vs)))
remove_idx = np.where(np.isnan(vs).any(axis=1))[0]

final_indices = np.array([i for i in idx if i not in remove_idx])
vs = np.array([vs[i] for i in idx if i not in remove_idx])

logging.info("fitting pca")
pca.fit(vs)
u = pca.components_

for i in trange(vs.shape[0], desc="moving vectors"):
    vs[i] = vs[i] - (u.T.dot(u)).dot(vs[i])

np.save(f'data/discourse_vectors_event_{event_name}_a_{a}.npy', arr=vs)
np.save(f'data/discourse_vectors_indices_{event_name}_a_{a}.npy', arr=final_indices)
# doc_vectors = np.load(f'fasttext_vectors_event_{event_name}.npy')
