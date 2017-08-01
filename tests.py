from mock.tweet import Tweet, URL
from document_generation.documents import join_tweets, get_representants, compute_groups_stats
from pprint import pprint

tweet_urls = {
    1: [(Tweet(t_id=1, retweet_of_id=None, in_reply_to_status_id=None, rt_count=10, fav_count=1),
         URL(url_id=1))],
    2: [(Tweet(t_id=2, retweet_of_id=1, in_reply_to_status_id=None, rt_count=10, fav_count=2),
         URL(url_id=None))],
    3: [(Tweet(t_id=3, retweet_of_id=None, in_reply_to_status_id=4, rt_count=1, fav_count=20),
         URL(url_id=None))],
    4: [(Tweet(t_id=4, retweet_of_id=None, in_reply_to_status_id=5, rt_count=1, fav_count=1),
         URL(url_id=None))],
    5: [(Tweet(t_id=5, retweet_of_id=None, in_reply_to_status_id=6, rt_count=1, fav_count=1),
         URL(url_id=None))],
    6: [(Tweet(t_id=6, retweet_of_id=None, in_reply_to_status_id=None, rt_count=1, fav_count=1),
         URL(url_id=3))],
    7: [(Tweet(t_id=7, retweet_of_id=2, in_reply_to_status_id=None, rt_count=1, fav_count=1),
         URL(url_id=1))],
    8: [(Tweet(t_id=8, retweet_of_id=1, in_reply_to_status_id=None, rt_count=1, fav_count=1),
         URL(url_id=None))],
    9: [(Tweet(t_id=9, retweet_of_id=None, in_reply_to_status_id=None, rt_count=1, fav_count=1),
         URL(url_id=2))],
    10: [(Tweet(t_id=10, retweet_of_id=None, in_reply_to_status_id=None, rt_count=1, fav_count=1),
          URL(url_id=2))],
    11: [(Tweet(t_id=11, retweet_of_id=None, in_reply_to_status_id=None, rt_count=1, fav_count=1),
          URL(url_id=3))],
    12: [(Tweet(t_id=12, retweet_of_id=123, in_reply_to_status_id=120, rt_count=1, fav_count=1),
          URL(url_id=40))],
    13: [(Tweet(t_id=13, retweet_of_id=None, in_reply_to_status_id=666, rt_count=1, fav_count=1),
          URL(url_id=None)),
         (Tweet(t_id=13, retweet_of_id=None, in_reply_to_status_id=666, rt_count=1, fav_count=1),
          URL(url_id=1))]
}

groups = join_tweets(tweet_urls)
# [[1, 2, 7, 8, 13], [3, 4, 5, 6, 11], [9, 10], [12], [13]]

print()
print("tweets:")
pprint(tweet_urls)
print()

print("groups")
pprint(groups)
print()

print("group stats")
pprint(compute_groups_stats(groups, tweet_urls))
print()

print("reps")
pprint([rep for rep in get_representants(groups, tweet_urls)])
print()
print()


from nlp.tokenizer import Tokenizer

tokenizer = Tokenizer()
text = "RT @microsoft: hi this is #apple #hashtag obama #care"

for token in tokenizer.tokenize(text, allow_urls=True, allow_hashtags=True, allow_mentions=True):
    print(token)