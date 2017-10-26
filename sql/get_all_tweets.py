
import logging

from sqlalchemy.orm import sessionmaker

from db import events
from db.engines import connect_to_server
from nlp.filter_tweets import filter_tweets
from nlp.tokenizer import Tokenizer
from db.models_cuboid import *
from document_generation.documents import get_representatives

logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s | %(name)s | %(levelname)s : %(message)s', level=logging.INFO)

m3 = lambda: connect_to_server(username='mquezada',
                               host="m3.dcc.uchile.cl",
                               ssh_pkey="/home/2015/mquezada/.ssh/id_rsa",
                               db_user="mquezada",
                               db_name="mquezada_db",
                               db_password="phoophoh7ahdaiJahphoh3aicooz7uka3ahJe9oi")

with m3() as engine:
    Session = sessionmaker(engine, autocommit=True)
    session = Session()

    for component_id in range(1, 25481 + 1):
        events = session.query(ComponentEvent).filter(ComponentEvent.component_id == component_id).all()

    #all_tweets = session.query(Tweet).yield_per(100000).filter(Tweet.event_id_id ==)

