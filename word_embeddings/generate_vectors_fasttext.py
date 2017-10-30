from db.models_new import *
from db.engines import engine_of215 as engine
from sqlalchemy.orm import sessionmaker
import logging
from db.events import get_documents_from_event

import spacy
import settings
from operator import itemgetter
from collections import defaultdict
from tqdm import tqdm
import time
import re

import numpy as np
import spacy

# load pre-trained vectors
from gensim.models import KeyedVectors


import sys

# event_name = sys.argv[1]
event_name = "hurricane_irma2"

logging.basicConfig(format='%(asctime)s | %(name)s | %(levelname)s : %(message)s', level=logging.INFO)
Session = sessionmaker(engine, autocommit=True)
session = Session()

nlp = spacy.load('en', parser=False, tagger=False, entity=False)

event_name = 'hurricane_irma'
documents = get_documents_from_event(event_name, session)

path = '/home/mquezada/phd/multimedia-summarization/data/ft_alltweets_model.vec'
w2v = KeyedVectors.load_word2vec_format(path)

doc_stream = nlp.pipe([doc.text for doc in documents[:, 0]], n_threads=16)
doc_vectors = np.empty((len(documents), w2v.vector_size))

for i, doc in tqdm(enumerate(doc_stream), total=len(documents)):
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
            doc_vector.append(w2v[token.lower_])

    # representative vector is the average of all words
    vector = np.mean(doc_vector, axis=0)[None]

    doc_vectors[i] = vector

np.save(f'data/fasttext_vectors_event_{event_name}.npy', arr=doc_vectors)
# doc_vectors = np.load(f'fasttext_vectors_event_{event_name}.npy')