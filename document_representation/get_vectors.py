from db import events
import numpy as np

from sklearn.feature_extraction.text import TfidfVectorizer
from nlp.tokenizer import Tokenizer

def get_fasttext_vectors(event_name, session):
    documents = events.get_documents_from_event(event_name, session)
    documents = documents[:, 0]

    doc_vectors = np.load(f'data/fasttext_vectors_event_{event_name}.npy')

    # all indices
    idx = range(len(doc_vectors))
    remove_idx = np.where(np.isnan(doc_vectors).any(axis=1))[0]

    input_vectors = [doc_vectors[i] for i in idx if i not in remove_idx]
    documents = np.array([documents[i] for i in idx if i not in remove_idx])

    return input_vectors, documents


def get_tfidf_vectors(event_name, session):
    documents = events.get_documents_from_event(event_name, session)
    documents = documents[:, 0]

    tokenizer = Tokenizer()

    tfidf = TfidfVectorizer(sublinear_tf=True, max_df=0.5, stop_words='english')
    X = tfidf.fit_transform([doc.text for doc in documents])

    return X, tfidf


