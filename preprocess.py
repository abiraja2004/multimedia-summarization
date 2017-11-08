"""

crea consultas y preprocesa los datos
genera documentos en la BD para consultarlos mas rapido

workflow:

- seleccionar un evento e de la DB
- seleccionar tweets T de e
- eliminar duplicados (quasi duplicados?) de T => T'
- resolver URLs de T'' => U
- eliminar spam de T' => T''
- generar documentos D desde (U, T)
- obtener representantes de D => R
- Generar representacion vectorial de R => V
- Hacer clusters de V => C
- Ordenar clusters por impacto π(C)
- Obtener representantes desde C => R'
- Presentar R'
"""

import logging

from sqlalchemy.orm import sessionmaker

from db import events
from db.engines import engine_of215 as engine
from db.models_new import EventGroup
from document_generation.documents import get_representatives
from nlp.filter_tweets import filter_tweets
from nlp.tokenizer import Tokenizer

import sys

logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s | %(name)s | %(levelname)s : %(message)s', level=logging.INFO)
tokenizer = Tokenizer()
Session = sessionmaker(engine, autocommit=True)
session = Session()

# custom variables
event_name = sys.argv[1]
# event_name = 'libya_hotel'
filtering = False  # select tweets already filtered?
# filtered tweet == tweet with few hashtags / urls

save_documents = not filtering  # save documents (url_tweets) to database?
event = session.query(EventGroup).filter(EventGroup.name == event_name).first()
event_ids = list(map(int, event.event_ids.split(',')))

# LOAD DATA
# loads tweet objs, url objects and mappings between tweets and urls
tweets, urls, tweet_url, url_tweets = events.get_tweets_and_urls(event_name, event_ids, session, filtering=filtering)

if not filtering:
    # filter out tweets with several urls or hashtags: T => T'
    tweets2 = filter_tweets(tweets, tokenizer)
    # set tweets to is_filtered = 1 in DB
    events.set_filtered_tweets(tweets, session)

# select representative tweets for each URL
representatives = list(get_representatives(url_tweets, tweets))

if save_documents:
    events.save_documents(representatives, url_tweets, tweets, event, session)
