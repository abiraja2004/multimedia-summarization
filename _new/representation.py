from sklearn.feature_extraction.text import TfidfVectorizer
from tqdm import tqdm, trange
from gensim.models import KeyedVectors
from pathlib import Path
import logging
from tokenizer import Tokenizer
from sklearn.decomposition import PCA
from sklearn.externals import joblib
import db
import numpy as np


class LazyTokenizer:
    def __init__(self, cls):
        self.cls = cls
        self.instance = None

    def __call__(self, *args, **kwargs):
        if not self.instance:
            self.instance = self.cls()
        return self.instance.tokenize(args[0])


class LazyWordEmbeddings:
    def __init__(self, path, name):
        self.path = path
        self.__we = None
        self.vector_size = None
        self.name = name

    def load(self):
        if not self.__we:
            logger.info(f"loading {self.name} vectors")
            self.__we = KeyedVectors.load_word2vec_format(self.path)
            self.vector_size = self.__we.vector_size

    def __getitem__(self, item):
        return self.__we[item]

    def __contains__(self, item):
        return item in self.__we


logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s | %(name)s | %(levelname)s : %(message)s', level=logging.INFO)
FASTTEXT_DATA_DIR = '/home/mquezada/phd/multimedia-summarization/data/word_embeddings/ft_alltweets_model.vec'
GLOVE_DATA_DIR = '/media/mquezada/HAHAHA/ams-data/glove.twitter.27B/glove.twitter.27B.200d.w2v'


def identity(x):
    return x


tokenizer = LazyTokenizer(Tokenizer)
ft = LazyWordEmbeddings(FASTTEXT_DATA_DIR, 'fasttext')
glove = LazyWordEmbeddings(GLOVE_DATA_DIR, 'glove')


def average_we(eventgroup_id: int, full: bool, overwrite=True, use_glove=False):
    if use_glove:
        name = 'glove'
        model = glove
    else:
        name = 'fasttext'
        model = ft

    if full:
        fname = f'data/{eventgroup_id}_{name}_full.pkl'
    else:
        fname = f'data/{eventgroup_id}_{name}.pkl'

    path = Path(fname)
    if path.exists() and not overwrite:
        logger.info(f"file {path.as_posix()} exists")
        return joblib.load(path)

    threshold = 0.5  # at least 50% of words should be in WE

    logger.info(f"loading documents (full={full})")
    docs = db.get_documents(eventgroup_id, full)
    keys, values = docs.keys(), docs.values()
    texts = [' '.join(d.text for d in doc_list) for doc_list in values]

    model.load()

    vectors_ = np.zeros((len(docs), model.vector_size), dtype=np.float32)
    doc_ids = []
    for i, (doc_id, t) in tqdm(enumerate(zip(keys, texts)), total=len(keys)):
        doc_vector = []
        total_words = 0
        for token in tokenizer(t):
            total_words += 1
            if token in model:
                doc_vector.append(model[token])

        if total_words > 0 and len(doc_vector) / total_words >= threshold:
            vectors_[i] = np.mean(doc_vector, axis=0)[None]
            doc_ids.append(doc_id)

    vectors = np.array([vectors_[i] for i in range(len(vectors_)) if not np.allclose(vectors_[i], 0)])
    rep_params = {'name': name}
    joblib.dump((vectors, doc_ids, rep_params), fname)
    return vectors, doc_ids, rep_params


def discourse(eventgroup_id: int, full: bool, alpha=0.001, overwrite=False, use_glove=False):
    if use_glove:
        name = 'glove'
        model = glove
    else:
        name = 'fasttext'
        model = ft

    if full:
        fname = f'data/{eventgroup_id}_discourse_{alpha}_{name}_full.pkl'
    else:
        fname = f'data/{eventgroup_id}_discourse_{alpha}_{name}.pkl'
    path = Path(fname)
    if path.exists() and not overwrite:
        logger.info(f"file {path.as_posix()} exists")
        return joblib.load(path)

    threshold = 0.5  # at least 50% of words should be in WE

    logger.info(f"loading documents (full={full})")
    docs = db.get_documents(eventgroup_id, full)
    keys, values = docs.keys(), docs.values()
    texts = [' '.join(d.text for d in doc_list) for doc_list in values]

    model.load()

    logger.info("loading freqs info")
    freq_path = '/home/mquezada/phd/multimedia-summarization/data/word_embeddings/wordfrequencies_relative.tsv'
    freqs = dict()
    with open(freq_path) as f:
        for line in f:
            word, freq = line.split()
            freqs[word] = float(freq)

    pca = PCA(n_components=1)

    vectors_ = np.zeros((len(docs), model.vector_size))
    doc_ids = []
    for i, (doc_id, t) in tqdm(enumerate(zip(keys, texts)), total=len(keys)):
        doc_vector = []
        total_words = 0
        for token in tokenizer(t):
            total_words += 1
            if token in model:
                wv = model[token]
                pw = freqs[token]

                doc_vector.append(alpha / (alpha + pw) * wv)

        if total_words > 0 and len(doc_vector) / total_words >= threshold:
            vectors_[i] = np.mean(doc_vector, axis=0)[None]
            doc_ids.append(doc_id)

    to_remove = [idx for idx in range(len(docs))
                 if np.allclose(vectors_[idx], np.zeros((1, model.vector_size)))]
    vectors = np.array([vectors_[i] for i in range(len(docs)) if i not in to_remove])

    logging.info("fitting pca")
    pca.fit(vectors)
    u = pca.components_

    for i in trange(vectors.shape[0], desc="moving vectors"):
        if i not in to_remove:
            vectors[i] = vectors[i] - (u.T.dot(u)).dot(vectors[i])

    params = {'a': alpha, 'name': f'discourse_{alpha}_{name}'}
    joblib.dump((vectors, doc_ids, params), fname)
    return vectors, doc_ids, params


def tfidf(eventgroup_id: int, full: bool, overwrite=False, use_glove=False):
    if full:
        fname = f'data/{eventgroup_id}_tfidf_full.pkl'
    else:
        fname = f'data/{eventgroup_id}_tfidf.pkl'
    path = Path(fname)
    if path.exists() and not overwrite:
        logger.info(f"file {path.as_posix()} exists")
        return joblib.load(path)

    logger.info(f"loading documents (full={full})")
    docs = db.get_documents(eventgroup_id, full)
    texts = [' '.join(d.text for d in doc_list) for doc_list in docs.values()]

    logger.info("applying tf-idf")
    vectorizer = TfidfVectorizer(tokenizer=tokenizer,
                                 preprocessor=identity,
                                 dtype=np.float32)

    m = vectorizer.fit_transform(texts)

    logger.info("saving matrix")
    params = vectorizer.get_params()
    params.pop('preprocessor')
    params.pop('tokenizer')
    params.pop('dtype')
    params['name'] = 'tf-idf'

    joblib.dump((m, list(docs.keys()), params), fname)
    return m, list(docs.keys()), params
