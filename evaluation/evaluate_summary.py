from pathlib import Path

import numpy as np
from nltk import TweetTokenizer
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from sqlalchemy.orm import sessionmaker

import settings
from baselines.kmeans import filter_tweet
from db.engines import engine_lmartine as engine
from db.events import get_tweets
from db.models_new import EventGroup
from evaluation import automatic_evaluation

"""
Evaluates the diversity of the summary, using jaccard and cosine similarity between the selected messages in
the summary
"""

tknzr = TweetTokenizer()
stop_words = set(stopwords.words('english'))
stop_words.update(
    ['~', '.', ':', ',', ';', '?', '¿', '!', '¡', '...', '/', '\'', '\\', '\"', '-', 'amp', '&', 'rt', '[', ']',
     '":', '--&',
     '(', ')', '|', '*', '+', '%', '$', '_', '@', 's', 'ap', '=', '}', '{', '**', '--', '()', '!!', '::', '||',
     '.:', ':.', '".', '))', '((', '’'])

vectorizer = TfidfVectorizer(stop_words=stop_words, dtype='float32')


def get_text_tweets(event_name):
    Session = sessionmaker(engine, autocommit=True)
    session = Session()
    event = session.query(EventGroup).filter(EventGroup.name == event_name).first()
    ids = list(map(int, event.event_ids.split(',')))
    tweets = get_tweets(event_name, ids, session)
    tweets_text = [tweet.text for tweet in tweets if filter_tweet(tweet.text)]
    return tweets_text


def calculate_cosine_similarity(lines):
    tfidf = vectorizer.fit_transform(lines)
    distances = ((tfidf * tfidf.T).A)
    triu = np.triu(distances, 1)
    triu[triu == 0] = np.nan
    print(f'Cosine {np.nanmean(triu)} {np.nanmax(triu)} {np.nanmin(triu)} {np.nanmedian(triu)}')


def calculate_jaccard(tokens, threshold):
    jaccard_score = []
    count = 0
    for i in range(len(tokens)):
        tokens_aux = tokens[i + 1:]
        scores_line = np.array(np.zeros(len(tokens)))
        for j in range(len(tokens_aux)):
            score = dist_jaccard_list(tokens[i], tokens_aux[j])
            if score > threshold:
                count = count + 1
            scores_line[j] = score
        jaccard_score.append(scores_line)
    print(
        f'Jaccard {np.array(jaccard_score).mean()} {np.array(jaccard_score).max()} {np.array(jaccard_score).min()} {np.median(np.array(jaccard_score))} {count}')
    return jaccard_score, count


def dist_jaccard_list(list1, list2):
    set1 = set(list1)
    set2 = set(list2)
    return float(len(set1 & set2)) / len(set1 | set2)


event_name = 'libya_hotel'
path_summaries = Path(settings.LOCAL_DATA_DIR_2, 'data', event_name, 'summaries', 'system')
summaries_file = [file for file in path_summaries.iterdir() if file.is_file()]
threshold = 0.6
# calculate_cosine_similarity(get_text_tweets(event_name))
for summary_file in summaries_file:
    tokens_summaries = []
    with summary_file.open('r') as summary:
        lines = summary.readlines()
        lines = [line for line in lines if line != '\n' or line != '']
        for line in lines:
            tokens = automatic_evaluation.remove_and_stemming(line, True)
            tokens_summaries.append(tokens)

        print(f'{summary_file.name}')
        calculate_jaccard(tokens_summaries, threshold)
        calculate_cosine_similarity(lines)
