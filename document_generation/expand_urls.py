"""

expand_urls(spacy_model, tweets: listOf(text), n_threads (opt)):

expande las urls de una lista de tweets
retorna un diccionario de short_url: (long_url, title)

"""

import spacy

from typing import Dict, List
import bs4

import logging
from queue import Queue
from threading import Thread

import requests
from requests.exceptions import TooManyRedirects, ReadTimeout, ConnectTimeout, ConnectionError


logger = logging.getLogger(__name__)


def get_urls_from_doc(doc: spacy.tokens.doc.Doc):
    for token in doc:
        if token.like_url:
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
            return resp.url, title
    except TooManyRedirects:
        logger.error(f"URL {url} too many redirects")
    except ReadTimeout:
        logger.error(f"URL {url} read timeout")
    except ConnectTimeout:
        logger.error(f"URL {url} connect timeout")
    except ConnectionError:
        logger.error(f"URL {url} connect error")
    except:
        logger.error("Other exception")


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


def expand_urls(spacy_model: spacy.en.English, tweet_texts: List[str], n_threads: int = 4):
    urls = set()

    logger.info(f"Extracting urls from {len(tweet_texts)} tweets")
    for doc in spacy_model.pipe(tweet_texts, n_threads=n_threads):
        for url in get_urls_from_doc(doc):
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
    return expanded_urls
