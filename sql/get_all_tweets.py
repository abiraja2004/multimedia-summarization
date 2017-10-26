
import logging

from sqlalchemy.orm import sessionmaker

from db.engines import connect_to_server
import spacy
from tqdm import trange
import re
from operator import itemgetter
from collections import Counter
from db.models_cuboid import *

logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s | %(name)s | %(levelname)s : %(message)s', level=logging.INFO)

logger.info("loading spacy model")
nlp = spacy.load('en', parser=False, tagger=False, entity=False)

m3 = lambda: connect_to_server(username='mquezada',
                               host="m3.dcc.uchile.cl",
                               ssh_pkey="/home/2015/mquezada/.ssh/id_rsa",
                               db_user="mquezada",
                               db_name="mquezada_db",
                               db_password="phoophoh7ahdaiJahphoh3aicooz7uka3ahJe9oi")

wc = Counter()

with m3() as engine, open('all_tweets_1_line_1_component.txt', 'w') as f:
    Session = sessionmaker(engine, autocommit=True)
    session = Session()

    for component_id in trange(1, 25481 + 1):
        event_ids = session.query(ComponentEvent.event_id).filter(ComponentEvent.component_id == component_id).all()
        event_ids = list(map(itemgetter(0), event_ids))
        all_texts = session.query(Tweet.text).yield_per(100000).filter(Tweet.event_id_id.in_(event_ids))

        texts = map(itemgetter(0), all_texts)

        for text in nlp.pipe(texts, batch_size=10000, n_threads=8):
            indexes = [m.span() for m in re.finditer('#\w+', text.text, flags=re.IGNORECASE)]
            for start, end in indexes:
                text.merge(start_idx=start, end_idx=end)

            for token in text:
                if token.pos_ == "PUNCT" or \
                        token.is_punct or \
                        token.is_space or \
                        token.text.startswith('@') or \
                        token.like_url:
                    continue

                wc[token.lower_] += 1
                f.write(token.lower_ + ' ')

        f.write('\n')
