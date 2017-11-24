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


class LazyCounter:
    def __init__(self, path):
        self.path = path
        self.__freqs = None

    def load(self):
        if not self.__freqs:
            self.__freqs = dict()
            with open(self.path) as f:
                for line in f:
                    word, freq = line.split()
                    self.__freqs[word] = float(freq)

    def __getitem__(self, item):
        return self.__freqs[item]

    def __contains__(self, item):
        return item in self.__freqs


class DocsCache:
    def __init__(self):
        self.docs = None
        self.eid = None
        self.full = None

    def get(self, eventgroup_id, full):
        if eventgroup_id != self.eid or full != self.full:
            self.docs = db.get_documents(eventgroup_id, full)
            return self.docs
        else:
            return self.docs


logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s | %(name)s | %(levelname)s : %(message)s', level=logging.INFO)
FASTTEXT_DATA_DIR = '/home/mquezada/phd/multimedia-summarization/data/word_embeddings/ft_alltweets_model.vec'
GLOVE_DATA_DIR = '/media/mquezada/HAHAHA/ams-data/glove.twitter.27B/glove.twitter.27B.200d.w2v'


def identity(x):
    return x


def precheck(name, eventgroup_id, use_glove, use_full, overwrite):
    vname = 'fasttext'
    model = ft
    if use_glove:
        vname = 'glove'
        model = glove

    fname = f'data/representation_{name}_{eventgroup_id}_{vname}.pkl'
    if use_full:
        fname = f'data/representation_{name}_{eventgroup_id}_{vname}_full.pkl'

    path = Path(fname)
    if path.exists() and not overwrite:
        logger.info(f"file {path.as_posix()} exists")
        return None

    return model, vname, fname


tokenizer = LazyTokenizer(Tokenizer)
ft = LazyWordEmbeddings(FASTTEXT_DATA_DIR, 'fasttext')
glove = LazyWordEmbeddings(GLOVE_DATA_DIR, 'glove')
freqs = LazyCounter('/home/mquezada/phd/multimedia-summarization/data/word_embeddings/wordfrequencies_relative.tsv')
docs_cache = DocsCache()


def average_we(eventgroup_id, use_full, use_glove, overwrite):
    cont = precheck("avg", eventgroup_id, use_glove, use_full, overwrite)
    if not cont:
        return
    model, vname, fname = cont

    threshold = 0.5  # at least 50% of words should be in WE
    logger.info(f"loading documents (full={use_full})")
    docs = docs_cache.get(eventgroup_id, use_full)
    total_docs = len(docs)

    logger.info(f'loading model (glove={use_glove})')
    model.load()

    vectors = []
    doc_ids = []

    for doc_id, texts in tqdm(docs.items(), total=total_docs, desc="computing vector avgs"):
        doc_vector = []
        total_words = 0

        for token in tokenizer(' '.join([d.text for d in texts])):
            total_words += 1
            if token in model:
                doc_vector.append(model[token])

        if total_words > 0 and len(doc_vector) / total_words >= threshold:
            vectors.append(np.mean(doc_vector, axis=0))
            doc_ids.append(doc_id)

    vectors = np.array(vectors, dtype=np.float32)
    rep_params = {'name': vname}
    joblib.dump((vectors, doc_ids, rep_params), fname)


def discourse(eventgroup_id, use_full, use_glove, overwrite, alpha=0.001):
    threshold = 0.5  # at least 50% of words should be in WE
    cont = precheck(f"disc-{alpha}", eventgroup_id, use_glove, use_full, overwrite)
    if not cont:
        return
    model, vname, fname = cont

    logger.info(f"loading documents (full={use_full})")
    docs = docs_cache.get(eventgroup_id, use_full)
    total_docs = len(docs)

    logger.info(f'loading model (glove={use_glove})')
    model.load()

    logger.info("loading freqs info")
    freqs.load()

    pca = PCA(n_components=1)
    vectors = []
    doc_ids = []
    for doc_id, texts in tqdm(docs.items(), total=total_docs, desc="computing vectors"):
        doc_vector = []
        total_words = 0

        for token in tokenizer(' '.join([d.text for d in texts])):
            total_words += 1

            if token in model:
                wv = model[token]
                pw = freqs[token]

                doc_vector.append(alpha / (alpha + pw) * wv)

        if total_words > 0 and len(doc_vector) / total_words >= threshold:
            vectors.append(np.mean(doc_vector, axis=0))
            doc_ids.append(doc_id)

    vectors = np.array(vectors, dtype=np.float32)
    logging.info("fitting pca")
    pca.fit(vectors)
    u = pca.components_

    for i in trange(vectors.shape[0], desc="moving vectors"):
        vectors[i] = vectors[i] - (u.T.dot(u)).dot(vectors[i])

    params = {'a': alpha, 'name': f'discourse_{alpha}_{vname}'}
    joblib.dump((vectors, doc_ids, params), fname)
    return vectors, doc_ids, params


def tfidf(eventgroup_id, use_full, use_glove, overwrite):
    fname = f'data/representation_tf-idf_{eventgroup_id}.pkl'
    if use_full:
        fname = f'data/representation_tf-idf_{eventgroup_id}_full.pkl'

    path = Path(fname)
    if path.exists() and not overwrite:
        logger.info(f"file {path.as_posix()} exists")
        return

    logger.info(f"loading documents (full={use_full})")
    docs = docs_cache.get(eventgroup_id, use_full)
    total_docs = len(docs)

    token_sets = []
    doc_ids = []
    for doc_id, texts in tqdm(docs.items(), total=total_docs, desc="tokenizing docs"):
        doc = []

        for token in tokenizer(' '.join([d.text for d in texts])):
            doc.append(token)

        if doc:
            token_sets.append(doc)
            doc_ids.append(doc_id)

    logger.info("applying tf-idf")
    vectorizer = TfidfVectorizer(tokenizer=identity,
                                 preprocessor=identity,
                                 dtype=np.float32)

    m = vectorizer.fit_transform(token_sets)

    logger.info("saving matrix")
    params = vectorizer.get_params()
    params.pop('preprocessor')
    params.pop('tokenizer')
    params.pop('dtype')
    params['name'] = 'tf-idf'

    joblib.dump((m, doc_ids, params), fname)

