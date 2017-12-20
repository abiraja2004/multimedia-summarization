import re
from pathlib import Path

from sqlalchemy.orm import sessionmaker
from tqdm import tqdm

import settings
from db.engines import engine_lmartine as engine
from db.models_new import Tweet

'''Save the text of the summary, some tweets are not available to be embbebed'''

Session = sessionmaker(engine, autocommit=True)
session = Session()

event_names = ['libya_hotel', 'oscar_pistorius', 'nepal_earthquake', 'hurricane_irma2']
for name in event_names:
    path_summaries = Path(settings.LOCAL_DATA_DIR_2, 'data', name, 'summaries', 'system')
    list_files = [file for file in Path(path_summaries, 'ids').iterdir() if file.is_file()]

    for file in tqdm(list_files):
        with file.open('r') as f:
            ids = f.readlines()
            tweets_unique = []

            for id in ids:
                tweet = session.query(Tweet).filter(Tweet.tweet_id == id).distinct().first()
                tweets_unique.append(tweet.text)

            with Path(path_summaries, 'text', f'{file.name[:-4]}_text.txt').open('w') as text_file:
                tweet_text = [re.sub(r"@\w+", '', re.sub(r"http\S+", '', text.replace('#', '').replace('\n', ''))) + '\n' for text in
                              tweets_unique]
                text_file.writelines(tweet_text)
