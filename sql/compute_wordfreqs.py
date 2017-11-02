from collections import Counter
from tqdm import tqdm
from multiprocessing import Pool
import os

data_dir = "data/all_tweets_1_line_1_component.txt"

wordfreqs = Counter()

with open(data_dir) as f:
    for line in tqdm(f):
        for w in line[:-1].split():
            wordfreqs[w] += 1

with open('data/wordfrequencies.tsv', 'w') as f:
    for w, freq in wordfreqs.items():
        f.write(f"{w}\t{freq}\n")

with open('data/wordfrequencies_relative.tsv', 'w') as f:
    total = sum(wordfreqs.values())
    for w, freq in wordfreqs.items():
        f.write(f"{w}\t{freq / total}\n")


# in parallel
def worker(fn):
    wordfreqs = Counter()

    with open(fn) as f:
        for line in tqdm(f):
            for w in line[:-1].split():
                wordfreqs[w] += 1
    return wordfreqs

path = '/media/mquezada/HAHAHA/ams-data/all_tweets/'
files = os.listdir(path)
for fn in files:
    with Pool(9) as p:
        counters = p.map(worker, [path + fn for fn in files])

