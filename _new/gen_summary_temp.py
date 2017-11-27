from summary import gen_summary2
from pathlib import Path
from sklearn.externals import joblib
from tqdm import tqdm
from models import *
import db

clusters_path = Path('data/clusters/').glob('*.pkl')


for fname in tqdm(clusters_path):
    print(fname.split('/')[-1])
    model, info, doc_ids = joblib.load(fname)
    name = db.get_eventgroup_name(info['event'])

    cluster = db.session.query(Cluster).filter(Cluster.id == info['cluster_id']).first()

    gen_summary2(event_name=name, cluster=cluster, model=model, info=info, doc_ids=doc_ids, session=db.session)
