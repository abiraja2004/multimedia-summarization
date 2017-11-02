import numpy as np
from scipy.sparse import lil_matrix

from tqdm import trange


class OnlineClustering:
    def __init__(self, tau=.7):
        self.tau = tau
        self.labels_ = None

    def fit(self, docs: np.array):
        n = docs.shape[0]

        d = docs @ docs.T
        # docs * docs es element-wise product
        norm = np.sqrt((docs * docs).sum(1, keepdims=True))

        # cos(vi, vj) = ((vi * vj) / ||vi||) / ||vj||
        s = (d / norm) / norm.T

        del d
        del norm

        one = np.ones((n, 1), dtype='bool')
        i = 0

        c = lil_matrix((n, n), dtype='bool')
        c[0, 0] = True

        for j in trange(1, n):
            c[i + 1, j] = 1

            t = 1 / c.dot(one)
            t[t > 1] = 0

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

    def get_params(self):
        return {"tau": self.tau}
