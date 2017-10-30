from collections import namedtuple
from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, BigInteger, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

TWEET = 'tweet_2017'
EVENT = 'event_2017'
USER = 'user_2017'
EVENT_TWEET = 'event_tweet_2017'

tweet_tuple = namedtuple('tweet_tuple', ['tweet', 'is_headline', 'event_id'])
Base = declarative_base()


class EventTweet(Base):
    __tablename__ = EVENT_TWEET

    id = Column(Integer, primary_key=True)
    tweet_id = Column(BigInteger, index=True)
    event_id = Column(Integer, index=True)
    when_added = Column(DateTime, default=datetime.now)


class Event(Base):
    __tablename__ = EVENT

    id = Column(Integer, primary_key=True)
    keyword1 = Column(String(255), index=True)
    keyword2 = Column(String(255), index=True)
    keyword3 = Column(String(255), index=True)
    when_added = Column(DateTime, default=datetime.now, index=True)


class Tweet(Base):

    __tablename__ = TWEET

    id = Column(Integer, primary_key=True)
    tweet_id = Column(BigInteger, index=True)  # == id
    text = Column(String(1024))
    created_at = Column(DateTime)  # e.g. "Wed Aug 27 13:08:45 +0000 2008"

    when_added = Column(DateTime, default=datetime.now)

    source = Column(String(255))
    source_url = Column(String(1024))
    entities = Column(Text)
    lang = Column(String(255))
    truncated = Column(Boolean)
    possibly_sensitive = Column(Boolean)

    coordinates = Column(String(255))
    # place == Place

    in_reply_to_status_id = Column(BigInteger)
    in_reply_to_screen_name = Column(String(255))
    in_reply_to_user_id = Column(BigInteger)

    favorite_count = Column(Integer)
    retweet_count = Column(Integer)

    is_headline = Column(Boolean)

    quoted_status_id = Column(BigInteger, nullable=True)

    is_a_retweet = Column(Boolean)
    retweeted_status_id = Column(BigInteger, nullable=True)

    user_id = Column(BigInteger)

    # is_filtered if the tweet is to be considered for summarization
    is_filtered = Column(Boolean, default=False)

    # was the tweet processed for resolving the url?
    url_expanded = Column(Boolean, default=False)

    def __repr__(self):
        return f'<Tweet [id={self.tweet_id}, text="{self.text}"]>'

    def __str__(self):
        return self.__repr__()


class User(Base):
    __tablename__ = USER

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, index=True)  # id
    verified = Column(Boolean)

    when_added = Column(DateTime, default=datetime.now)

    name = Column(String(255))
    screen_name = Column(String(255), index=True)
    created_at = Column(DateTime)

    description = Column(String(2048))
    location = Column(String(512))
    geo_enabled = Column(Boolean)
    entities = Column(Text)
    lang = Column(String(255))
    url = Column(String(255))

    followers_count = Column(Integer)
    favourites_count = Column(Integer)
    listed_count = Column(Integer)
    friends_count = Column(Integer)  # followings
    statuses_count = Column(Integer)

    utc_offset = Column(String(255))
    time_zone = Column(String(255))

    def __repr__(self):
        return f'<User [id={self.user_id}, screen_name={self.screen_name}]>'

    def __str__(self):
        return self.__repr__()


class Cluster(Base):
    __tablename__ = 'cluster'
    id = Column(Integer, primary_key=True)
    eventgroup_id = Column(Integer)
    json = Column(Text)


class DocumentCluster(Base):
    __tablename__ = 'document_cluster'

    id = Column(Integer, primary_key=True)
    document_id = Column(BigInteger)
    cluster_id = Column(Integer)
    label = Column(Integer)

    def __repr__(self):
        return f'<DocumentCluster [cluster_id={self.cluster_id}, label={self.label}]>'

    def __str__(self):
        return self.__repr__()


class Document(Base):
    __tablename__ = 'document'

    id = Column(Integer, primary_key=True)
    text = Column(String(512))
    tweet_id = Column(BigInteger)
    total_rts = Column(Integer)
    total_favs = Column(Integer)
    total_replies = Column(Integer)
    total_tweets = Column(Integer)
    embedded_html = Column(Text)
    expanded_url_id = Column(Integer)

    def __str__(self):
        return f"<Document [id={self.tweet_id}, text={self.text}>"

    def __repr__(self):
        return self.__str__()


class DocumentTweet(Base):
    __tablename__ = 'document_tweet'
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer)
    tweet_id = Column(Integer)


class TweetURL(Base):
    __tablename__ = 'tweet_url'

    id = Column(Integer, primary_key=True)
    tweet_id = Column(BigInteger)
    url_id = Column(Integer)

    def __str__(self):
        return f"<TweetURL [tweet_id={self.tweet_id}, url_id={self.url_id}]>"

    def __repr__(self):
        return self.__str__()


class ShortURL(Base):
    __tablename__ = 'short_url'

    id = Column(Integer, primary_key=True)
    short_url = Column(String(255))
    expanded_id = Column(Integer)

    def __str__(self):
        return f"<ShortURL [id={self.id}, url={self.short_url}, exp={self.expanded_id}]>"

    def __repr__(self):
        return self.__str__()


class ExpandedURL(Base):
    __tablename__ = 'expanded_url'

    id = Column(Integer, primary_key=True)
    expanded_url = Column(String(2048))
    title = Column(String(2048))
    expanded_clean = Column(String(2048))

    def __str__(self):
        return f"<URL [id={self.id}, url={self.expanded_clean[:-1]}]>"

    def __repr__(self):
        return self.__str__()


class EventGroup(Base):
    __tablename__ = 'eventgroup'

    id = Column(Integer, primary_key=True)
    name = Column(String(1024))
    event_ids = Column(String(2048))

    def __str__(self):
        return f"<EventGroup [name={self.name}, ids={self.event_ids}]>"

    def __repr__(self):
        return self.__str__()


class DocumentGroup(Base):
    __tablename__ = 'document_eventgroup'

    id = Column(Integer, primary_key=True)
    document_id = Column(Integer)
    eventgroup_id = Column(Integer)
