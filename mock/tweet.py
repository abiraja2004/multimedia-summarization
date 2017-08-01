

class Tweet:
    def __init__(self, t_id,
                 retweet_of_id=None,
                 in_reply_to_status_id=None,
                 rt_count=0,
                 fav_count=0):

        self.tweet_id = t_id
        self.retweet_of_id = retweet_of_id
        self.in_reply_to_status_id = in_reply_to_status_id

        self.retweet_count = rt_count
        self.favorite_count = fav_count

    def __repr__(self):
        return f"<id={self.tweet_id}, " \
               f"rt_of={self.retweet_of_id}, " \
               f"reply_of={self.in_reply_to_status_id}>"


class URL:
    def __init__(self, url_id=None):
        self.id = url_id

    def __repr__(self):
        return f"<url_id={self.id}>"
