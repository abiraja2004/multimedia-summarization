from sqlalchemy.orm import sessionmaker

from db.engines import engine_lmartine as engine
from db.events import get_tweets
from db.models_new import EventGroup


def exploration(event_name, ids, session):
    tweets = get_tweets(event_name, ids, session)

    originals = 0
    retweets = 0
    replies = 0
    for tweet in tweets:
        if tweet.is_a_retweet:
            retweets = retweets + 1
        elif tweet.in_reply_to_status_id is not None:
            replies = replies + 1
        else:
            originals = originals + 1

    print('Total tweets: {}'.format(len(tweets)))
    print('originals: {}'.format(originals))
    print('retweets: {}'.format(retweets))
    print('replies: {}'.format(replies))


if __name__ == '__main__':
    Session = sessionmaker(engine, autocommit=True)
    session = Session()
    events_names = ['libya_hotel', 'oscar_pistorius', 'nepal_earthquake', 'hurricane_irma2']
    for event_name in events_names:
        event = session.query(EventGroup).filter(EventGroup.name == event_name).first()
        event_ids = list(map(int, event.event_ids.split(',')))
        exploration(event_name, event_ids, session)
