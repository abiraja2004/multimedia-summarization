"""Convert the info in the old database in the new schema"""
from collections import defaultdict

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from tqdm import tqdm

from db.engines import engine_lmartine as engine_new
from db.models_new import Event as Event_new
from db.models_new import ShortURL, ExpandedURL, EventTweet, EventGroup
from db.models_new import Tweet as Tweet_new
from db.models_new import TweetURL as TweetURL_new
from db.models_old_ams import Tweet, URL, TweetURL, Event

engine = create_engine('mysql://root:oracle_753@localhost/ams')

Session = sessionmaker(engine, autocommit=True)
session = Session()


Session_new = sessionmaker(engine_new, autocommit=True)
session_new = Session_new()


def load_tweets():
    tweets = session.query(Tweet).all()
    with session_new.begin():
        for tweet in tqdm(tweets):
            new_tweet = Tweet_new(tweet_id=tweet.tweet_id, text=tweet.text, created_at=tweet.created_at,
                                  source=tweet.source,
                                  entities=tweet.entities, lang=tweet.lang, coordinates=tweet.coordinates,
                                  in_reply_to_status_id=tweet.in_reply_to_status_id,
                                  in_reply_to_screen_name=tweet.in_reply_to_screen_name,
                                  in_reply_to_user_id=tweet.in_reply_to_user_id, favorite_count=tweet.favorite_count,
                                  retweet_count=tweet.retweet_count,
                                  is_a_retweet=tweet.is_retweet, retweeted_status_id=tweet.retweet_of_id)
            session_new.add(new_tweet)


def load_urls():
    urls = session.query(URL).all()
    tweets_urls = session.query(TweetURL).all()
    with session_new.begin():
        for (url, tweet_url) in tqdm(zip(urls, tweets_urls)):
            expanded_url = ExpandedURL(expanded_url=url.expanded_url, title=url.title,
                                       expanded_clean=url.expanded_clean)
            session_new.add(expanded_url)
            session_new.flush()
            short_url = ShortURL(short_url=url.short_url, expanded_id=expanded_url.id)
            session_new.add(short_url)
            session_new.flush()
            tweet_url_new = TweetURL_new(tweet_id=tweet_url.tweet_id, url_id=short_url.id)
            session_new.add(tweet_url_new)
            # session_new.flush()


def load_events():
    events = session.query(Event).all()
    tweets = session.query(Tweet).all()
    inserted_events = defaultdict(set)
    with session_new.begin():
        for event in tqdm(events):
            event_new = Event_new(keyword1=event.title)
            session_new.add(event_new)
            inserted_events[event.event_id].add(event_new)
            # session.commit()

    with session_new.begin():
        for tweet in tqdm(tweets):
            event_tweet = EventTweet(tweet_id=tweet.tweet_id, event_id=list(inserted_events[tweet.event_id_id])[0].id)
            session_new.add(event_tweet)

            # events_new = session_new.query(Event_new).filter(Event_new.id.in_(list(set_ids))).all()
            # ids = defaultdict(list)
            # for event in tqdm(events_new):
            #     ids[event.keyword1].append(event.id)
            # for key, value in ids.items():
            #     event_group = EventGroup(key, value)
            #     session_new.add(event_group)


def load_eventgroup():
    event_added = ['oscar_pistorius', 'libya_hotel', 'nepal_earthquake', 'mumbai_rape']
    for keyword in tqdm(event_added):
        events = session_new.query(Event_new).filter(Event_new.keyword1 == keyword).all()
        ids = [event.id for event in events]
        event_group = EventGroup(name=keyword, event_ids=ids.__str__().replace('[', '').replace(']', ''))
        session_new.add(event_group)


# load_tweets()
# load_urls()
# load_events()
load_eventgroup()
