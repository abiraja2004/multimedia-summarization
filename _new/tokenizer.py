import re
import logging
import spacy
from multiprocessing import cpu_count

HASHTAG_PLACEHOLDER = 'ZZZPLACEHOLDERZZZ'


class Tokenizer:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.info("Loading spacy model")
        self.nlp = spacy.load('en_core_web_sm', parser=False, tagger=False, entity=False, matcher=False)
        self.logger.info("Model Loaded")

    def tokenize(self, text,
                 allow_urls=False,
                 allow_stop=False,
                 allow_hashtags=False,
                 allow_mentions=False):
        text_ht = re.sub(r'#(\w+)', rf'{HASHTAG_PLACEHOLDER}\1', text)
        doc = self.nlp(text_ht)
        for token in doc:
            if (not allow_stop and token.is_stop) \
                    or (not allow_urls and token.like_url) \
                    or (not allow_mentions and token.text.startswith('@')) \
                    or (not allow_hashtags and token.text.startswith(HASHTAG_PLACEHOLDER)) \
                    or token.pos_ == 'PUNCT' \
                    or token.is_punct \
                    or token.is_space:
                    # or token.lemma_.lower() in stopwords \
                    # or token.ent_type_ not in allowed_entities:
                continue
            else:
                if token.text.startswith(HASHTAG_PLACEHOLDER):
                    yield token.lower_
                else:
                    yield token.text.lower()

    def count_special_tokens(self, texts):
        """
        counts hashtags and urls for each text in texts
        :param texts:
        :return: Iterator: (# hashtags, # urls) for each text
        """

        for doc in self.nlp.pipe(texts, n_threads=4):
            no_url = 0
            no_htg = 0

            tokens = list(doc)
            bigrams = zip(tokens, tokens[1:] + tokens[0:1])

            for bigram in bigrams:
                if bigram[0].like_url:
                    no_url += 1
                if bigram[0].text == '#':
                    no_htg += 1

            yield (no_htg, no_url)
