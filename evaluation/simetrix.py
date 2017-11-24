import re
import subprocess
from pathlib import Path

from nltk import FreqDist, TweetTokenizer
from nltk.corpus import stopwords
from sqlalchemy.orm import sessionmaker
from tqdm import tqdm

import settings
from db import events
from db.engines import engine_lmartine as engine
from db.models_new import EventGroup, Tweet

tknzr = TweetTokenizer()


def create_input_dir(event_name, event_ids, session):
    tweets = events.get_tweets(event_name, event_ids, session)
    tweets_text = [re.sub(r"@\w+", '', re.sub(r"http\S+", '', tweet.text.replace('#', ''))) + '\n' for tweet in tweets]
    with Path('data_simetrix', event_name, f'input_{event_name}.txt').open('w') as tweets_file:
        tweets_file.writelines(tweets_text)


def create_mappings(event_name):
    summaries = [file for file in Path(settings.LOCAL_DATA_DIR_2, 'data', event_name, 'summaries', 'system').iterdir()
                 if file.is_file()]
    source = Path('data_simetrix', event_name, f'input_{event_name}.txt')
    with Path('data_simetrix', 'mappings.txt').open('a') as mappings:
        for summary in summaries:
            line = f'{event_name} {summary.name[:-4]} {source.absolute()} {summary.absolute()} \n'
            mappings.write(line)


def calculate_background_corpus(session):
    tweets = session.query(Tweet).all()
    tweets_text = [re.sub(r"@\w+", '', re.sub(r"http\S+", '', tweet.text.replace('#', ''))) for tweet in tweets]
    stop_words = set(stopwords.words('english'))
    stop_words.update(
        ['~', '.', ':', ',', ';', '?', '¿', '!', '¡', '...', '/', '\'', '\\', '\"', '-', 'amp', '&', 'rt', '[', ']',
         '":', '--&',
         '(', ')', '|', '*', '+', '%', '$', '_', '@', 's', 'ap', '=', '}', '{', '**', '--', '()', '!!', '::', '||',
         '.:', ':.', '".', '))', '((', '’'])

    list_tokens = [[i.lower() for i in tknzr.tokenize(text) if i.lower() not in stop_words] for text in tweets_text]
    words = []
    for tokens in tqdm(list_tokens):
        for word in tokens:
            word = word.replace('\n', '').replace(' ', '').replace('.', '')
            if word not in stop_words and not word == '':
                words.append(word.replace('\n', '').replace(' ', ''))
    fdist_all = FreqDist(words)
    with Path('data_simetrix', 'bgFreqCounts.unstemmed.txt').open('w') as background_corpus:
        for word, count in tqdm(fdist_all.items()):
            background_corpus.write(f'{word} {count} \n')

    return fdist_all


if __name__ == '__main__':
    Session = sessionmaker(engine, autocommit=True)
    session = Session()

    events_names = ['libya_hotel', 'nepal_earthquake', 'oscar_pistorius', 'hurricane_irma2']

    if not Path('data_simetrix', 'bgFreqCounts.unstemmed.txt').exists():
        calculate_background_corpus(session)

    for name in events_names:
        event = session.query(EventGroup).filter(EventGroup.name == name).first()
        event_ids = list(map(int, event.event_ids.split(',')))

        input_dir = Path('data_simetrix', name)
        if not input_dir.exists():
            input_dir.mkdir()
            create_input_dir(name, event_ids, session)

        print("Creating Mapping file")
        create_mappings(name)

    subprocess.call(
        ['java', '-jar', 'simetrix.jar', 'data_simetrix/mappings.txt', 'data_simetrix/config.example'])
