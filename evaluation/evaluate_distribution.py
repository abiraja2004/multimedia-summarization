import re
from pathlib import Path

import dit
from dit.divergences import jensen_shannon_divergence
from nltk import TweetTokenizer
from sqlalchemy.orm import sessionmaker

import db.datasets
from db.engines import engine_lmartine as engine
from db.events import get_tweets
from evaluation.automatic_evaluation import calculate_vocab_distribution, calculate_most_popular
from settings import LOCAL_DATA_DIR_2

'''
Evaluate the distribution of words in a event, comparing the all the tweets of an event with the timeline.
'''

tknzr = TweetTokenizer()


def calculate_distribution_event(event_name, session, event_ids, steam=False):
    """
    Calculate the word distribution using all the tweets of an event. Also removes hashtags
    user mentions and urls.
    :param session:
    :param steam:
    :param event_name: name of the event
    :return: words, all words sorted by probability; distribution, probabilities of the words
            pairs, tuple of (word, probability)
    """
    tweets = get_tweets(event_name, event_ids, session)
    text = '\n'
    for tweet in tweets:
        tweet_text = re.sub(r"@\w+", '', re.sub(r"http\S+", '', tweet.text.replace('#', '')))
        text += tweet_text + '\n'
    words, distribution, pairs = calculate_vocab_distribution(text, steam)
    return words, distribution, pairs


def calculate_distribution_timeline(event_name, timeline):
    """
    Calculate the word distribution of a specific timeline.
    :param event_name: Name of the event
    :param timeline: Name of the file, that contains the timeline.
    :return: words, all words sorted by probability; distribution, probabilities of the words
            pairs, tuple of (word, probability)
    """
    reference = Path(LOCAL_DATA_DIR_2, 'data', event_name, 'summaries', 'reference', timeline)
    with reference.open('r') as f:
        words, distribution, pairs = calculate_vocab_distribution(f.read())
        # print(pairs)
    return words, distribution, pairs


def global_distribution(references_list):
    """
    Calculate the distribution of words, considering the concatenation of all timelines for the event
    :param references_list: list with the name of the files with the timelines.
    :return: words, all words sorted by probability; distribution, probabilities of the words
            pairs, tuple of (word, probability)
    """
    total_reference = ''
    for reference in references_list:
        with reference.open() as f:
            total_reference = total_reference + f.read()
    words, probs, pairs = calculate_vocab_distribution(total_reference)
    total_distribution = dit.ScalarDistribution(words, probs)
    return total_distribution, words


def evaluate_coverage_tweets(event, n_words, session, ids):
    """
    Evaluate the coverage between the tweets in the summary and all the tweets of an event.
    Only consider de n most popular words.
    :param ids:
    :param event: Name of the event
    :param n_words: Number of words to consider.
    :return: Jaccard Index for the n most popular words
    """
    print('-------- {} ------------'.format(event))
    summaries_path = Path(LOCAL_DATA_DIR_2, 'data', event, 'summaries', 'system')
    summaries = [x for x in summaries_path.iterdir() if x.is_file()]
    words, distribution, pairs = calculate_distribution_event(event, session, ids, steam=True)
    print(words[:n_words])
    for summary in summaries:
        with open(summary, 'r') as summary_file:
            print(summary_file.name)
            text_summary = summary_file.read()
            popular_summary = calculate_most_popular(text_summary, n_words, steam=True)
            popular_words = [x[0] for x in popular_summary]
            print(popular_words)
            print(
                float(len(set(words[:n_words]) & set(popular_words))) / len(set(words[:n_words]) | set(popular_words)))


def evaluate_distibution(event_name, words, session, ids):
    """
    Do a complete evaluation of the distribution of words for an event. Compute Jensen-Shannon
    and  Jaccard Index
    :param event_name: Name of the event to be evaluated
    :return:
    """
    print(event_name, words)
    words_event, distribution_event, pairs_event = calculate_distribution_event(event_name, session, ids, True)
    path_references = Path(LOCAL_DATA_DIR_2, 'data', event_name, 'summaries', 'reference')
    references_list = [reference for reference in path_references.iterdir() if reference.is_file()]
    event_dist = dit.ScalarDistribution(words_event, distribution_event)
    words_set_event = set(words_event[:words])
    print('Most Common words in event: {}'.format(words_set_event))
    total_dist, all_words = global_distribution(references_list)
    all_words_set = set(all_words[:words])
    jaccard = len(words_set_event.intersection(all_words_set)) / len(words_set_event.union(all_words_set))
    print('Most Common words in all timelines: {}'.format(all_words_set))
    print('Jaccard Index with all timelines: {}'.format(jaccard))
    print('Jensen-Shannon with all timelines: {}'.format(jensen_shannon_divergence([total_dist, event_dist])))
    for reference in references_list:
        words_timeline, probs_timeline, pairs_timeline = calculate_distribution_timeline(event_name, reference)
        dist_timeline = dit.ScalarDistribution(words_timeline, probs_timeline)
        print('----------------------------')
        word_set_timeline = set(words_timeline[:words])
        print(reference.name)
        print('Most Common words in timeline: {}'.format(word_set_timeline))
        print('Jensen-Shannon: {}'.format(jensen_shannon_divergence([dist_timeline, event_dist])))
        jaccard = len(words_set_event.intersection(word_set_timeline)) / len(words_set_event.union(word_set_timeline))
        print('Jaccard Index: {}'.format(jaccard))


if __name__ == '__main__':
    Session = sessionmaker(engine, autocommit=True)
    session = Session()
    n_words = [10, 15, 20, 25, 35]
    event_ids = db.datasets.libya_hotel
    for n_word in n_words:
        print('n_words: {}'.format(n_word))
        # evaluate_coverage_tweets('oscar_pistorius', n_word)
        evaluate_coverage_tweets('libya_hotel', n_word, session, event_ids)
        # evaluate_coverage_tweets('nepal_earthquake', n_word)

    evaluate_distibution('libya_hotel', 15, session, event_ids)
    evaluate_distibution('libya_hotel', 20, session, event_ids)
