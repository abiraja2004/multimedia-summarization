"""

expand_urls(spacy_model, tweets: listOf(text), n_threads (opt)):

expande las urls de una lista de tweets
retorna un diccionario de short_url: (long_url, title)

"""

import spacy

from typing import Dict, List, Tuple, Iterable
import bs4

import logging
from queue import Queue
from threading import Thread
from urllib import parse
from db.models_new import Tweet
from collections import defaultdict

import requests
from requests.exceptions import TooManyRedirects, ReadTimeout, ConnectTimeout, ConnectionError


logger = logging.getLogger(__name__)


def clean_url(url: str) -> str:
    u = parse.urldefrag(url).url
    u = parse.urlparse(u)
    query = parse.parse_qs(u.query)
    allowed = ('v', 'id', 'fbid', 'contentguid', 'set', 'type', 'l')
    query = {k: v for (k, v) in query.items() if k in allowed}
    u = u._replace(query=parse.urlencode(query, True))
    return parse.urlunparse(u)


def get_urls_from_doc(doc: spacy.tokens.doc.Doc):
    for token in doc:
        if token.like_url:
            if len(token.text) < 14:  # filter out invalid urls
                continue
            yield token


def resolve_url(url):
    try:
        resp = requests.get(url, allow_redirects=True, timeout=5)
        if resp and resp.ok:
            html = bs4.BeautifulSoup(resp.text, "html5lib")
            title = None
            if html:
                title = html.title or ''
                title = ' '.join(title.text.split())
                title = title[:1024]
            return resp.url, title, clean_url(resp.url)
    except TooManyRedirects:
        logger.error(f"URL <{url}> - too many redirects")
    except ReadTimeout:
        logger.error(f"URL <{url}> - read timeout")
    except ConnectTimeout:
        logger.error(f"URL <{url}> - connect timeout")
    except ConnectionError:
        logger.error(f"URL <{url}> - connect error")
    except:
        logger.error(f"URL <{url}> - other error")


def worker(q: Queue, result: Dict):
    while True:
        url = q.get()
        if url is None:
            q.task_done()
            break
        url_title = resolve_url(url)
        if url_title:
            result[url] = tuple(url_title)
        q.task_done()


def expand_urls(spacy_model: spacy.en.English, tweets: List[Tweet], n_threads: int = 8) \
        -> Tuple[Dict[str, Tuple[str, str, str]], Dict[int, List[str]]]:

    urls = set()
    shorturl_tweetid = defaultdict(list)
    tweet_texts = [tweet.text for tweet in tweets]
    tweet_ids = [tweet.tweet_id for tweet in tweets]

    logger.info(f"Extracting urls from {len(tweet_texts)} tweets")
    for tweet_id, doc in zip(tweet_ids, spacy_model.pipe(tweet_texts, n_threads=n_threads)):
        short_urls = list(get_urls_from_doc(doc))

        for u in short_urls:
            shorturl_tweetid[u].append(tweet_id)

        for url in short_urls:
            urls.add(url)

    q = Queue()
    threads = []
    expanded_urls = dict()
    total = len(urls)

    logger.info(f'Spawning {n_threads} threads')
    for _ in range(n_threads):
        t = Thread(target=worker, args=(q, expanded_urls))
        t.start()
        threads.append(t)

    logger.info(f"Adding {total} urls to queue")
    for url in urls:
        q.put(url)

    q.join()

    logger.info(f'Done')
    for __ in range(n_threads):
        q.put(None)

    logger.info('Joining threads')
    for t in threads:
        t.join()

    logger.info("Exiting main thread")
    return expanded_urls, shorturl_tweetid
