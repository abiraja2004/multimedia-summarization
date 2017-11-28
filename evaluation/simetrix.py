import re
import subprocess
from math import log
from pathlib import Path

from nltk import FreqDist, TweetTokenizer
from nltk.corpus import stopwords
from sqlalchemy.orm import sessionmaker
from tqdm import tqdm

import settings
from db import events
from db.engines import engine_lmartine as engine
from db.models_new import EventGroup
from evaluation.automatic_evaluation import remove_and_stemming

tknzr = TweetTokenizer()

stop_words = set(stopwords.words('english'))
stop_words.update(
    ['~', '.', ':', ',', ';', '?', '¿', '!', '¡', '...', '/', '\'', '\\', '\"', '-', 'amp', '&', 'rt', '[', ']',
     '":', '--&',
     '(', ')', '|', '*', '+', '%', '$', '_', '@', 's', 'ap', '=', '}', '{', '**', '--', '()', '!!', '::', '||',
     '.:', ':.', '".', '))', '((', '’'])


def create_input_dir(event_name, event_ids, session):
    tweets = events.get_tweets(event_name, event_ids, session)
    tweets_text = [re.sub(r"@\w+", '', re.sub(r"http\S+", '', tweet.text.replace('#', ''))) + '\n' for tweet in tweets]
    with Path('data_simetrix', event_name, f'input_{event_name}.txt').open('w') as tweets_file:
        tweets_file.writelines(tweets_text)


def create_mappings(event_name):
    summaries = [file for file in Path(settings.LOCAL_DATA_DIR_2, 'data', event_name, 'summaries', 'system').iterdir()
                 if file.is_file()]
    source = Path('data_simetrix', event_name, f'input_{event_name}.txt')
    # source = Path(settings.LOCAL_DATA_DIR_2, 'data', event_name, 'summaries', 'reference')
    with Path('data_simetrix', 'mappings.txt').open('a') as mappings:
        for summary in summaries:
            line = f'{event_name} {summary.name[:-4]} {source.absolute()} {summary.absolute()} \n'
            mappings.write(line)


def calculate_idf_background(session, tweets_text):
    # tweets_text = get_tweets_text(session)
    docs_size = len(tweets_text)
    counts_words = {}
    for text in tqdm(tweets_text):
        tokens = remove_and_stemming(text)
        for token in tokens:
            token = token.replace('\n', '').replace(' ', '').replace('.', '').replace('\t', '')
            if not token == '':
                if token in counts_words.keys():
                    counts_words[token] = counts_words[token] + 1
                else:
                    counts_words[token] = 1

    with Path('data_simetrix', 'bgIdfFreq.stemmed.txt').open('w') as idf_backgroud:
        idf_backgroud.write(str(docs_size) + '\n')
        for word, count in counts_words.items():
            idf_value = log(docs_size / (1 + count))
            idf_backgroud.write(f'{word} {idf_value} \n')


def calculate_background_corpus(session, tweets_text):
    #tweets_text = get_tweets_text(session)
    list_tokens = [[i.lower() for i in tknzr.tokenize(text) if i.lower() not in stop_words] for text in tweets_text]
    words = []
    for tokens in tqdm(list_tokens):
        for word in tokens:
            word = word.replace('\n', '').replace(' ', '').replace('.', '').replace('\t', '')
            if word not in stop_words and not word == '':
                words.append(word.replace('\n', '').replace(' ', ''))
    fdist_all = FreqDist(words)
    with Path('data_simetrix', 'bgFreqCounts.unstemmed.txt').open('w') as background_corpus:
        for word, count in tqdm(fdist_all.items()):
            background_corpus.write(f'{word} {count} \n')

    return fdist_all


def get_tweets_text(session):
    tweets = []
    for name in tqdm(events_names):
        event = session.query(EventGroup).filter(EventGroup.name == name).first()
        event_ids = list(map(int, event.event_ids.split(',')))
        tweets_event = events.get_tweets(name, event_ids, session)
        tweets.extend(tweets_event)
    tweets_text = [re.sub(r"@\w+", '', re.sub(r"http\S+", '', tweet.text.replace('#', ''))) for tweet in tweets]
    return tweets_text


if __name__ == '__main__':
    Session = sessionmaker(engine, autocommit=True)
    session = Session()

    # events_names = ['hurricane_irma2', 'oscar_pistorius', 'nepal_earthquake', 'libya_hotel']
    events_names = ['hurricane_irma2']
    if not Path('data_simetrix', 'bgFreqCounts.unstemmed.txt').exists():
        tweets_text = get_tweets_text(session)
        calculate_background_corpus(session, tweets_text)
        calculate_idf_background(session, tweets_text)

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
