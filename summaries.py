import json
import logging
from pathlib import Path

from sqlalchemy.orm import sessionmaker
from tqdm import tqdm

# from db.engines import engine_lmartine as engine
from db import events
from db.engines import connect_to_server
from db.models_new import Document, Cluster, DocumentCluster

event_name = "irma"

logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s | %(name)s | %(levelname)s : %(message)s', level=logging.INFO)
# tokenizer = Tokenizer()

number_summaries = 5

# server, engine = connect_from_rafike(username='mquezada', password='100486')
connect = lambda: connect_to_server(username="lmartinez", host="172.17.69.88", ssh_pkey="/home/luis/.ssh/id_rsa")
with connect() as engine:
    Session = sessionmaker(engine, autocommit=True)
    session = Session()

    # documents = session.query(Document).all()
    documents = events.get_documents_from_event(event_name, session)
    results_dir = Path('results', 'results_more_tweets')

    html_template = '''<blockquote class="twitter-tweet" data-lang="en">
      <a href="https://twitter.com/jack/status/%s"></a>
    </blockquote>'''
    script = '<script async src="http://platform.twitter.com/widgets.js" charset="utf-8"></script>'


    def cmp(d: Document):
        # return d.total_favs + d.total_replies + d.total_rts + d.total_tweets
        return d.total_rts


    clusters = session.query(Cluster).all()

    for i, cluster in tqdm(enumerate(clusters), total=len(clusters)):
        document_cluster = session.query(Document, DocumentCluster) \
            .join(DocumentCluster, DocumentCluster.document_id == Document.id) \
            .filter(DocumentCluster.cluster_id == cluster.id).all()

        params = json.loads(cluster.json)

        with (results_dir / Path(f'cl_{"-".join(params["name"].split())}_{i}.html')).open('w') as f:
            f.write(f'<source>{cluster.json}</source>\n')

            # TODO sort filter clusters
            n_clusters = params['params']['n_clusters']
            n = 0
            for j in range(n_clusters):
                docs_in_cluster_j = [d for d, l in document_cluster if l.label == j]
                f.write("\n ----- Cluster {} Size: {} -----".format(n, len(docs_in_cluster_j)))
                # best_doc = max(docs_in_cluster_j, key=cmp)
                docs_in_cluster_j.sort(key=lambda x: x.total_rts, reverse=True)
                for doc in set(docs_in_cluster_j[:number_summaries]):
                    f.write(html_template % (str(doc.tweet_id)))
                n = n + 1

            f.write(script)
