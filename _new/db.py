from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import logging
from models import *
from collections import defaultdict
from typing import Dict, List, Union

engine = create_engine('mysql://root@localhost/twitter_news?charset=utf8mb4', encoding='utf-8')

logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s | %(name)s | %(levelname)s : %(message)s', level=logging.INFO)

Session = sessionmaker(engine, autocommit=True)
session = Session()


def get_eventgroup_id(event_name: str) -> EventGroup:
    return session.query(EventGroup).filter(EventGroup.name == event_name).first()

def get_eventgroup_name(event_id: int):
    return session.query(EventGroup).filter(EventGroup.id== event_id).first()

def get_documents(eventgroup_id: int, full=True) -> Dict[int, List[Union[Tweet, Document]]]:
    if full:
        q = session.query(Tweet, DocumentTweet) \
            .join(DocumentTweet, DocumentTweet.tweet_id == Tweet.tweet_id) \
            .join(Document, Document.id == DocumentTweet.document_id) \
            .filter(Document.eventgroup_id == eventgroup_id) \
            .filter(Tweet.is_filtered) \
            .yield_per(5000)

        docs = defaultdict(list)
        for t, dt in q:
            docs[dt.document_id].append(t)

    else:
        q = session.query(Document.id, Document) \
            .filter(Document.eventgroup_id == eventgroup_id) \
            .yield_per(5000)

        docs = defaultdict(list)
        for i, t in q:
            docs[i].append(t)

    return docs
