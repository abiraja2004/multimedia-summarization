from pathlib import Path

from db_utils import get_tweets_list

from evaluation.automatic_evaluation import dist_jaccard, calculate_most_popular, dist_jaccard_list
from settings import LOCAL_DATA_DIR_2


def get_tweets_summary(list_id):
    return get_tweets_list(list_id)


def process_file_mgraph(file_name, event_name):
    file_path = Path(LOCAL_DATA_DIR_2, 'data', event_name, 'summaries', 'system', file_name)
    with file_path.open('r') as file_mgraph:
        lines = file_mgraph.readlines()
        ids = [line.split('\t')[0] for line in lines]
        return get_tweets_summary(ids)


def process_file_system(file_name, event_name):
    file_path = Path(LOCAL_DATA_DIR_2, 'data', event_name, 'summaries', 'system', file_name)
    with file_path.open('r') as file_summary:
        return file_summary.readlines()


def compare_method(event_name, baseline_file, method_file):
    tweets_baseline = process_file_mgraph(baseline_file, event_name)
    tweets_summary = process_file_system(method_file, event_name)
    n_tweets = len(tweets_summary)
    text_baseline = [tweet.text for tweet in tweets_baseline[:n_tweets]]
    text_baseline = '\n'.join(text_baseline)
    text_summary = '\n'.join(tweets_summary)
    print(calculate_most_popular(text_baseline, 20, steam=True))
    print(calculate_most_popular(text_summary, 20, steam=True))
    popular_baseline = [pair[0] for pair in calculate_most_popular(text_baseline, 20, steam=True)]
    popular_summary = [pair[0] for pair in calculate_most_popular(text_summary, 20, steam=True)]
    print(dist_jaccard_list(popular_baseline, popular_summary))
    print(dist_jaccard(text_baseline, text_summary))


compare_method('libya_hotel', 'summary_mgraph.tsv', 'libyahotel_5_5.txt')
compare_method('libya_hotel', 'summary_mgraph.tsv', 'libyahotel_5_3.txt')
