from db import events
import numpy as np

import logging

from sklearn.feature_extraction.text import TfidfVectorizer
from nlp.tokenizer import Tokenizer


def get_fasttext_vectors(event_name, eventgroup_id, session, dtype='float32'):
    logging.info("loading documents from DB")
    id_tweets = events.get_documents_from_event2(eventgroup_id, session)

    doc_ids = {j: i for j, i in enumerate(id_tweets.keys())}

    logging.info(f"loading data from data/fasttext_vectors_event_{event_name}.npy")
    doc_vectors = np.load(f'data/fasttext_vectors_event_{event_name}.npy')

    # all indices
    idx = range(len(doc_vectors))
    remove_idx = np.where(np.isnan(doc_vectors).any(axis=1))[0]

    input_vectors = np.array([doc_vectors[i] for i in idx if i not in remove_idx])
    documents = np.array([doc_ids[i] for i in idx if i not in remove_idx])

    # documents = np.array([documents[i] for i in idx if i not in remove_idx])

    input_vectors = input_vectors.astype(dtype)

    logging.info("done loading documents")
    return input_vectors, documents


def get_tfidf_vectors(event_name, eventgroup_id, session):
    logging.info("loading documents from DB")
    documents = events.get_documents_from_event(event_name, session)
    documents = documents[:, 0]

    logging.info("generating tfidf vectors")
    tfidf = TfidfVectorizer(sublinear_tf=True, max_df=0.5, stop_words='english')
    X = tfidf.fit_transform([doc.text for doc in documents])

    return X.todense(), tfidf, [doc.id for doc in documents]


def get_discourse_vectors(event_name, eventgroup_id, a, session, dtype='float32'):
    logging.info("loading documents from DB")
    id_tweets = events.get_documents_from_event2(eventgroup_id, session)
    doc_ids = {j: i for j, i in enumerate(id_tweets.keys())}

    logging.info(f"loading data from {event_name} with param {a}")

    fname = f"data/discourse_vectors_event_{event_name}_a_{a}.npy"
    doc_vectors = np.load(fname)

    idx_name = f"data/discourse_vectors_indices_{event_name}_a_{a}.npy"
    indices = np.load(idx_name)

    documents = np.array([doc_ids[i] for i in indices])
    # documents = np.array([documents[i] for i in indices])
    doc_vectors = doc_vectors.astype(dtype)

    logging.info("done loading documents")
    return doc_vectors, documents

