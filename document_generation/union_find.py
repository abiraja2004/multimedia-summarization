class UnionFind:

    def __init__(self):
        self.groups = []
        self.parent = dict()
        self.rank = dict()

    def make_set(self, elem):
        self.parent[elem] = elem
        self.rank[elem] = 0
        self.groups.append(elem)

    def find(self, elem):
        if elem not in self.parent:
            return None

        if elem != self.parent[elem]:
            self.parent[elem] = self.find(self.parent[elem])
        return self.parent[elem]

    def union(self, u, v):
        root_u = self.find(u)
        root_v = self.find(v)

        if root_u == root_v or root_u is None or root_v is None:
            return

        if self.rank[root_u] > self.rank[root_v]:
            self.parent[root_v] = root_u
            self.groups.remove(root_v)
        else:
            self.parent[root_u] = root_v
            self.groups.remove(root_u)
            if self.rank[root_u] == self.rank[root_v]:
                self.rank[root_v] += 1

    def size(self):
        return len(self.groups)
