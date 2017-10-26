
import logging

from sqlalchemy.orm import sessionmaker

from db import events
from db.engines import connect_to_server
from nlp.filter_tweets import filter_tweets
from nlp.tokenizer import Tokenizer
from db.models_new import EventGroup
from document_generation.documents import get_representatives

logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s | %(name)s | %(levelname)s : %(message)s', level=logging.INFO)

# m3
server, engine = connect_to_server(username='mquezada',
                                   host="m3.dcc.uchile.cl",
                                   ssh_pkey="/home/2015/mquezada/.ssh/id_rsa",
                                   db_user="mquezada",
                                   db_name="mquezada_db",
                                   db_password="phoophoh7ahdaiJahphoh3aicooz7uka3ahJe9oi")

Session = sessionmaker(engine, autocommit=True)
session = Session()

