import re
from pathlib import Path

'''Clean and save the summary generated'''


def save_summary_text(event_name, docs, clustering, n_tweets, remove=True):
    path_summary = Path('data', event_name, 'summaries', 'system',
                        event_name.replace('_', '') + '_' + clustering + '_' + str(n_tweets) + '.txt')
    f = open(path_summary, 'a')
    if remove:
        docs = [re.sub(r"@\w+", '', re.sub(r"http\S+", '', x.url.replace('#', ''))) for x in docs]

    f.writelines([x + '\n' for x in docs])
    f.close()


def save_summary_ids(event_name, ids, clustering, n_tweets):
    pass
