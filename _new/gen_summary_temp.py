from summary import gen_summary2
from pathlib import Path, PosixPath
from sklearn.externals import joblib
from tqdm import tqdm
from models import *
import db

clusters_path = Path('data/clusters/').glob('*.pkl')


for fname in tqdm(list(clusters_path)):
    print(fname.as_posix().split('/')[-1])
    model, info = joblib.load(fname)
    name = db.get_eventgroup_name(info['event']).name

    cluster = db.session.query(Cluster).filter(Cluster.id == info['cluster_id']).first()

    gen_summary2(event_name=name, cluster_fname=fname, repr_fname=info['fname'].as_posix(), session=db.session)