"""
Do the automatic evaluation of the summaries.
Compare the selected tweets with a timeline extracted from internet.+
The summaries are in data/event_name/summaries/system, and the reference(gold standard) are
in data/event_name/summaries/reference
Calculate ROUGE, Jaccard Index and Jensen-Shannon
"""
import collections
import subprocess
from pathlib import Path

import dit
import jprops
from dit.divergences import jensen_shannon_divergence
from nltk import FreqDist
from nltk.corpus import stopwords
from nltk.stem.porter import *
from nltk.tokenize import TweetTokenizer

from settings import LOCAL_DATA_DIR_2

stemmer = PorterStemmer()
tknzr = TweetTokenizer()

path = '/home/luis/PycharmProjects/ams/Embeddings/model.vec'
# w2v = KeyedVectors.load_word2vec_format(path)
w2v = object()


def calculate_most_popular(text, n_populars, steam=False):
    """
    Calculate the n most popular words in a string
    :param text: String
    :param n_populars: number of words to consider.
    :return: List, the n most popular words of the text, sorted by decreasing popularity.
    """
    fdist = calculate_fdist(text, steam)
    term = []
    for key, value in fdist.items():
        term.append((key, value))
    term.sort(key=lambda x: int(x[1]), reverse=True)
    return term[:n_populars]


def calculate_fdist(text, stem=False):
    """
    Calculate the frequency distribution of a text
    :param text: String
    :param stem: bool, perform steaming in the text
    :return: Frequency distribution
    """
    list_of_words = remove_and_stemming(text, stem)
    fdist_all = FreqDist(list_of_words)
    return fdist_all


def remove_and_stemming(text, steam=False):
    """
    Remove stop words and steam text
    :param text: String to be processed
    :param steam:
    :return: List, list of words
    """
    stop_words = set(stopwords.words('english'))
    stop_words.update(
        ['~', '.', ':', ',', ';', '?', '¿', '!', '¡', '...', '/', '\'', '\\', '\"', '-', 'amp', '&', 'rt', '[', ']',
         '":', '--&',
         '(', ')', '|', '*', '+', '%', '$', '_', '@', 's', 'ap', '=', '}', '{', '**', '--', '()', '!!', '::', '||',
         '.:', ':.', '".', '))', '((', '’'])
    if steam:
        list_of_words = [stemmer.stem(i.lower()) for i in tknzr.tokenize(text) if i.lower() not in stop_words]
    else:
        list_of_words = [i.lower() for i in tknzr.tokenize(text) if i.lower() not in stop_words]
    return list_of_words


def calculate_vocab_distribution(text, steam=False):
    """
    Calculate the distribution of vocabulary in a text
    :param steam:
    :param text:
    :return: words, list of all words in text, probs, sorted list with the probabilities of each word
            pairs, list of tuples (word, probability)
    """
    fdist = calculate_fdist(text, steam)
    fdist = {k: v for k, v in fdist.items() if v > 1}
    len_vocab = sum(fdist.values())
    pairs = [(key, value / len_vocab) for key, value in fdist.items()]
    pairs.sort(key=lambda x: int(x[1]), reverse=True)
    return [x[0] for x in pairs], [x[1] for x in pairs], pairs


def create_distribution(event, reference_name, summary_name):
    path_reference = Path(LOCAL_DATA_DIR_2, 'data', event, 'summaries', 'reference', reference_name)
    path_summary = Path(LOCAL_DATA_DIR_2, 'data', event, 'summaries', 'system', summary_name)
    with path_reference.open('r') as reference, path_summary.open('r') as summary:
        reference_text = reference.read()
        summary_text = summary.read()
        summary_words, summary_probs, _ = calculate_vocab_distribution(summary_text)
        reference_words, reference_probs, _ = calculate_vocab_distribution(reference_text)
        summary_dist = dit.ScalarDistribution(summary_words, summary_probs)
        reference_dist = dit.ScalarDistribution(reference_words, reference_probs)
    return reference_dist, summary_dist


def compute_rouge(event):
    """
    Compute rouge-1 score for an event
    :param event: Name of the event
    :return:
    """
    summaries_path = Path(LOCAL_DATA_DIR_2, 'data', event, 'summaries')

    with open('rouge.properties', 'r+') as fp:
        props = jprops.load_properties(fp, collections.OrderedDict)
        ngrams = props.get('ngram')
        result_path = Path(LOCAL_DATA_DIR_2, 'data', event, 'summaries', 'result_rouge_ngram' + str(ngrams) + '.csv')
        props.pop('project.dir')
        props.pop('outputFile')
        props.update({'project.dir': str(summaries_path.absolute()), 'outputFile': str(result_path.absolute())})
        fp.seek(0)
        fp.truncate()
        jprops.store_properties(fp, props)

    subprocess.call(['java', '-jar', 'rouge2.0_0.2.jar', '-Drouge.prop=', 'rouge.properties'])


def compute_jensen_shannon(event, reference_name, summary_name):
    reference_dist, summary_dist = create_distribution(event, reference_name, summary_name)
    return jensen_shannon_divergence([summary_dist, reference_dist])


def dist_jaccard(str1, str2):
    str1 = set(remove_and_stemming(str1, True))
    str2 = set(remove_and_stemming(str2, True))
    return float(len(str1 & str2)) / len(str1 | str2)


def dist_jaccard_list(list1, list2):
    set1 = set(list1)
    set2 = set(list2)
    return float(len(set1 & set2)) / len(set1 | set2)


def compute_jaccard(event, reference_name, summary_name):
    path_reference = Path(LOCAL_DATA_DIR_2, 'data', event, 'summaries', 'reference', reference_name)
    path_summary = Path(LOCAL_DATA_DIR_2, 'data', event, 'summaries', 'system', summary_name)
    with path_reference.open('r') as reference, path_summary.open('r') as summary:
        reference_text = reference.read()
        summary_text = summary.read()
    return dist_jaccard(summary_text, reference_text), dist_jaccard(reference_text, summary_text)


def evaluate_event(event_name):
    print('-------------' + event_name + '--------------')

    compute_rouge(event_name)
    event_path = Path(LOCAL_DATA_DIR_2, 'data', event_name, 'summaries')
    references_path = Path(event_path, 'reference')
    summaries_path = Path(event_path, 'system')
    references = [x for x in references_path.iterdir() if x.is_file()]
    summaries = [x for x in summaries_path.iterdir() if x.is_file()]

    for reference in references:
        for summary in summaries:
            print(f'Jensen-Shannon: {compute_jensen_shannon(event_name, reference.name, summary.name)}')
            print(f'Jaccard Distance: {compute_jaccard(event_name, reference.name, summary.name)}')


if __name__ == '__main__':
    evaluate_event('libya_hotel')
    # evaluate_event('oscar_pistorius')
    # evaluate_event('nepal_earthquake')
