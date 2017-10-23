import logging
import sys
from tqdm import tqdm
import json

from sqlalchemy.orm import sessionmaker

from db.engines import engine_of215 as engine
from db.models_new import Document, Cluster, DocumentCluster
from pathlib import Path

event_name = sys.argv[1]

logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s | %(name)s | %(levelname)s : %(message)s', level=logging.INFO)
# tokenizer = Tokenizer()

# server, engine = connect_from_rafike(username='mquezada', password='100486')
Session = sessionmaker(engine, autocommit=True)
session = Session()

# documents = events.get_documents_from_event(event_name, session)
documents = session.query(Document).all()
results_dir = Path('results')

html_template = '''<blockquote class="twitter-tweet" data-lang="en">
  <a href="https://twitter.com/jack/status/%s"></a>
</blockquote>'''
script = '<script async src="http://platform.twitter.com/widgets.js" charset="utf-8"></script>'


def cmp(d: Document):
    #return d.total_favs + d.total_replies + d.total_rts + d.total_tweets
    return d.total_rts


clusters = session.query(Cluster).all()

for i, cluster in tqdm(enumerate(clusters), total=len(clusters)):
    document_cluster = session.query(Document, DocumentCluster) \
        .join(DocumentCluster, DocumentCluster.document_id == Document.id) \
        .filter(DocumentCluster.cluster_id==cluster.id).all()

    params = json.loads(cluster.json)

    with (results_dir / Path(f'cl_{"-".join(params["name"].split())}_{i}.html')).open('w') as f:
        f.write(f'<source>{cluster.json}</source>\n')

        # TODO sort filter clusters
        n_clusters = params['params']['n_clusters']

        for j in range(n_clusters):
            docs_in_cluster_j = [d for d, l in document_cluster if l.label == j]
            best_doc = max(docs_in_cluster_j, key=cmp)
            f.write(html_template % (str(best_doc.tweet_id)))

        f.write(script)
