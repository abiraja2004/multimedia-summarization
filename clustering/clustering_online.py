import numpy as np
from scipy.sparse import lil_matrix

from tqdm import trange


class OnlineClustering:
    def __init__(self, tau):
        self.tau = tau
        self.labels_ = None
        self.n_clusters = 0

    def fit(self, docs: np.array):
        n = docs.shape[0]

        d = docs @ docs.T
        # docs * docs es element-wise product
        norm = np.sqrt((docs * docs).sum(1, keepdims=True))

        # cos(vi, vj) = ((vi * vj) / ||vi||) / ||vj||
        s = (d / norm) / norm.T
        np.fill_diagonal(s, self.tau)

        del d
        del norm

        one = np.ones((n, 1), dtype='bool')
        i = 0

        c = lil_matrix((n, n), dtype='bool')
        c[0, 0] = True

        for j in trange(1, n):
            # elem j belongs to cluster i + 1
            c[i + 1, j] = 1

            # t := 1 / (# of elems in each cluster)
            t = 1 / c.dot(one)

            # inf values removed
            t[t > 1] = 0

            # sum of similarities of elem j to elems in each cluster
            v = c.dot(s[:, j])

            v = v * t.T

            v[v < self.tau] = 0

            k = np.argmax(v)

            c[i + 1, j] = 0
            c[k, j] = 1
            i += 1

        self.labels_ = np.zeros(n, dtype=np.uint32)
        c = c.tocoo()

        for i, j, _ in zip(c.row, c.col, c.data):
            self.labels_[j] = i

        self.n_clusters = int(max(self.labels_)) + 1
        return self

    def get_params(self):
        return {"tau": self.tau, "n_clusters": self.n_clusters}
