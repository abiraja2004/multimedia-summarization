from pathlib import Path

from pymongo import MongoClient

events = ['tweets_libya', 'tweets_oscar', 'tweets_nepal', 'tweets_irma']
client = MongoClient()
with Path('all_urls.txt').open('w') as urls_files:
    for event in events:
        count_url_event = 0
        db = client[event]
        collection = db.tweets_collection
        tweets = collection.find({"entities.media": {"$exists": True }})
        uniques = set()
        #print(len(tweets))
        for tweet in tweets:
            photos = tweet['entities']['media']
            for photo in photos:
                url = photo['media_url']
                uniques.add(url+'\n')
                count_url_event = count_url_event + 1
        urls_files.writelines(list(uniques))
        print(f'{event} {count_url_event}')