"""
modelos en sqlalchemy de las tablas existentes en cuboid:
tweet
cluster
document_cluster
document
document_tweet
tweet_url
url
"""


from sqlalchemy import Column, Integer, String, DateTime, BigInteger, Boolean
from sqlalchemy import Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Tweet(Base):
    __tablename__ = 'tweet'

    tweet_id = Column(BigInteger, primary_key=True)
    text = Column(String(140))
    in_reply_to_status_id = Column(BigInteger)
    favorite_count = Column(Integer)
    source = Column(String(255))
    coordinates = Column(String(255))
    entities = Column(String(255))
    in_reply_to_screen_name = Column(String(255))
    in_reply_to_user_id = Column(BigInteger)
    retweet_count = Column(Integer)
    is_retweet = Column(Boolean)
    retweet_of_id = Column(BigInteger)
    user_id_id = Column(BigInteger)
    lang = Column(String(255))
    created_at = Column(DateTime)
    event_id_id = Column(Integer)

    def __str__(self):
        return f"<id={self.tweet_id}, text={self.text}>"

    def __repr__(self):
        return self.__str__()


class ComponentEvent(Base):
    __tablename__ = "componentevent"

    id = Column(Integer, primary_key=True)
    component_id = Column(Integer)
    event_id = Column(Integer)


class Cluster(Base):
    __tablename__ = 'cluster'
    id = Column(Integer, primary_key=True)
    json = Column(Text)


class DocumentCluster(Base):
    __tablename__ = 'document_cluster'

    id = Column(Integer, primary_key=True)
    document_id = Column(BigInteger)
    cluster_id = Column(Integer)
    label = Column(Integer)


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

    def __str__(self):
        return f"<id={self.tweet_id}, text={self.url}, embebed_html={self.embedded_html}>"

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
        return f"<tweet_id={self.tweet_id}, url_id={self.url_id}>"

    def __repr__(self):
        return self.__str__()


class URL(Base):
    __tablename__ = 'url'

    id = Column(Integer, primary_key=True)
    short_url = Column(String(255))
    expanded_url = Column(String(1024))
    title = Column(String(1024))
    expanded_clean = Column(String(1024))

    def __str__(self):
        return f"<id={self.id}, short={self.short_url}, exp={self.expanded_url}, title={self.title}>"

    def __repr__(self):
        return self.__str__()


class Event(Base):
    __tablename__ = 'event'

    id = Column(Integer, primary_key=True)
    keywords = Column(String(255))
    datetime = Column(DateTime)
    featured = Column(Boolean)

    def __str__(self):
        return f'<id={self.id}, keywords={self.keywords}, date={self.datetime}'

    def __repr__(self):
        return self.__str__()


