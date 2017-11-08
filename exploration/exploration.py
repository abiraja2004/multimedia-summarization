from sqlalchemy.orm import sessionmaker

from db.engines import engine_lmartine as engine
from db.events import get_tweets_and_urls
from db.models_new import EventGroup


def exploration(event_name, ids, session):
    tweets, urls, tweets_urls, urls_tweets = get_tweets_and_urls(event_name, ids, session)

    print('Total URLs: {}'.format(len(urls.keys())))
    print('AVG URLs per Tweet: {}'.format(len(urls.keys()) / len(tweets.keys())))
    print('AVG tweets per URLs: {}'.format(len(tweets.keys()) / len(urls.keys())))

    originals = 0
    retweets = 0
    replies = 0
    for _, tweet in tweets.items():
        if tweet.is_a_retweet:
            retweets = retweets + 1
        elif tweet.in_reply_to_status_id is not None:
            replies = replies + 1
        else:
            originals = originals + 1

    print('Total tweets: {}'.format(len(tweets.keys())))
    print('originals: {}'.format(originals))
    print('retweets: {}'.format(retweets))
    print('replies: {}'.format(replies))


if __name__ == '__main__':
    Session = sessionmaker(engine, autocommit=True)
    session = Session()
    event_name = 'libya_hotel'
    event = session.query(EventGroup).filter(EventGroup.name == event_name).first()
    event_ids = list(map(int, event.event_ids.split(',')))
    exploration(event_name, event_ids, session)
