import sys
import math
import re
import logging
import itertools
import multiprocessing
import argparse
import pickle
import os

import wordsegment as ws
import numpy as np

from collections import Counter
from functools import reduce
from multiprocessing import Process, Manager
from multiprocessing.managers import BaseManager
from importlib import reload

from nltk.corpus import wordnet as wn
from nltk.corpus.reader.api import CorpusReader
from nltk.corpus.util import LazyCorpusLoader
from nltk.corpus.reader.wordnet import WordNetCorpusReader

from learning.pos import BackoffTagger, SpacyTagger, COCATagger
from learning.tagset_conversion import TagsetConverter
from learning.tree.wordnet import IndexedWordNetTree
from learning.model import TreeCutModel, Grammar, GrammarTagger

from pattern.text.en import pluralize, lexeme
from util.digits_pattern import digits
from misc.util import Timer

# load global resources

log = logging.getLogger(__name__)
tag_converter = TagsetConverter()
proper_noun_tags = set(BackoffTagger.proper_noun_tags())
ws.load()


def new_wordnet_instance():
    """
    Create a new wordnet instance. This is usefult for parallel workflows.
    Multiple processes cannot access the same wordnet instance (as when imported
    globally with `from wordnet.corpus import wordnet`). This is due nltk not
    being thread-safe.
    """
    return LazyCorpusLoader(
        'wordnet', WordNetCorpusReader,
        LazyCorpusLoader('omw', CorpusReader,
                         r'.*/wn-data-.*\.tab', encoding='utf8')
    )


def tally(password_file, lowercase=True):
    """Return a Counter for passwords."""
    pwditer = (line.rstrip('\n').lower() for line in password_file
               if not re.fullmatch(r'\s+', line))

    return Counter(pwditer)


def getchunks(password):
    # split into character/digit/symbols chunks
    temp = re.findall(r'([\W_]+|[a-zA-Z]+|[0-9]+)', password)

    # split character chunks into word chunks
    chunks = []
    for chunk in temp:
        if chunk[0].isalpha() and len(chunk) > 1:
            words = ws.segment(chunk)
            chunks.extend(words)
        elif chunk[0].isdigit():
            segments = digits.digit2chunk.get(chunk, [chunk])
            chunks.extend(segments)
        else:
            chunks.append(chunk)

    if len(chunks) == 0:
        log.warning("Unable to chunk password: {}".format(password))

    return chunks


def synset(word, pos, wordnet, tag_converter=None, min_length_n=3, min_length_v=2):
    """
    Given a POS-tagged word, determine its synset by converting the CLAWS tag
    to a WordNet tag and querying the associated synset from NLTK's WordNet.

    If more than one synset is retrieved, return the first, which is, presumably,
    the most frequent. More on this at:
    http://wordnet.princeton.edu/wordnet/man/cntlist.5WN.html

    If the fragment has no POS tag or no synset is found in WordNet for the POS
    tag, None is returned.

    - pos: a part-of-speech tag from the CLAWS7 tagset

    """

    if pos is None or pos in proper_noun_tags:
        return None

    wn_pos = tag_converter.clawsToWordNet(pos)

    if wn_pos is None:
        return None

    min_length = min_length_n if wn_pos == 'n' else min_length_v
    if len(word) < min_length:
        return None

    synsets = wordnet.synsets(word, wn_pos)

    return synsets[0] if len(synsets) > 0 else None


class POSBlacklist():
    def __init__(self):
        self.coca = COCATagger()

    def is_bad(self, word):
        return ((len(word) == 1 and word not in 'ai') or
                (word not in self.coca.tag_map) or
                (len(word) < 4 and word in self.coca.tag_map and
                 self.coca.tag_map[word][0][1] < 1000))


def pos_tag(tokens, tagger, blacklist):
    """ Assign POS tags to alphabetic tokens, except when they are short (less
    than 3 chars) AND have no adjacent tokens of the same type (e.g. "1ab!!").
    Such tokens are likely to be short strings in a random password.

    Example:
        >>> pos_tag(['i', 'love', 'you', '2'])
        [('i', 'ppis1'), ('love', 'vv0'), ('you', 'ppy'), ('2', None)]

        >>> train.pos_tag(['123','ab','!!'], tagger)
        [('123', None), ('ab', None), ('!!', None)]

    """
    if len(tokens) == 1:
        token = tokens[0]
        if token.isalpha():
            return tagger.tag(tokens)
        else:
            return [(token, None)]

    # try to tag only consecutive sequences of alphabetic non-blacklisted tokens
    # (which are likely to be non-random)
    # assign None to isolated alpha tokens and all other types of tokens

    tags = []
    alpha_mask = [c[0].isalpha() for c in tokens]

    buffer = []  # records adjacent tokens of the same type
    for i, isalpha in enumerate(alpha_mask):
        # if we find a token that isn't alpha, then tag whatever is
        # accumulated in the buffer
        if not isalpha or \
                blacklist and blacklist.is_bad(tokens[i]):
            if len(buffer) > 0:
                tags.extend(tagger.tag(buffer))
                buffer = []

            tags.append((tokens[i], None))
        # if this alpha token has an adjacent alpha token, it should be tagged
        elif len(alpha_mask) > i + 1 and alpha_mask[i + 1] or \
                i > 0 and alpha_mask[i - 1]:
            buffer.append(tokens[i])
        elif len(tokens[i]) > 2:
            buffer.append(tokens[i])
        else:  # it's alpha but short and isolated, then None
            tags.append((tokens[i], None))

    if len(buffer) > 0:
        tags.extend(tagger.tag(buffer))

    return tags


def lemmas(synset):
    lemmas = wn.synset(synset).lemmas()
    lemmas = [l.name() for l in lemmas]
    return lemmas


def noun_vocab(tcm=None, postagger=None, min_length=0):
    """
    Return all nouns found in wordnet in both singular and plurar forms,
    along with POS tag and synset (as given by a TreeCutModel instance).
    """
    if not postagger:
        postagger = BackoffTagger()

    getpostag = lambda word: postagger.tag([word])[0][1]
    singular_n_pos = getpostag("house")
    plural_n_pos = getpostag("houses")

    nouns = set()

    for lemma in wn.all_lemma_names(pos='n'):
        if len(lemma) < min_length:
            continue
        if '_' in lemma:
            continue

        plural = None
        if lemma[-1] != 's':
            plural = pluralize(lemma)
            # use the the plural only if it still enable us to
            # get to the synsets (some words shouldn't be pluralized)
            if len(wn.synsets(plural)) == 0:
                plural = None

        for syn in wn.synsets(lemma, 'n'):
            classes = tcm.predict(syn) if tcm is not None else [syn.name()]
            for classy in classes:
                nouns.add((lemma, singular_n_pos, classy))
                if plural is not None:
                    nouns.add((plural, plural_n_pos, classy))

    return nouns


def verb_vocab(tcm=None, postagger=None, min_length=0):
    """
    Return all verbs found in wordnet in various inflected forms.
    """
    if not postagger:
        postagger = BackoffTagger.from_pickle()

    getpostag = lambda word: postagger.tag([word])[0][1]

    # Most of the time lexeme() returns 4 or 5 words, inflected as declared below
    # To avoid assumptions on the tagset used, we query the tags using easy examples
    # (verb give). These POS tags are then bound to lexeme's results.
    infinitive_pos = getpostag("give")
    present_pos = getpostag("gives")
    pres_prog_pos = getpostag("giving")
    past_pos = getpostag("gave")
    past_prog_pos = getpostag("given")

    # three possibilities for return of function tenses
    # depending on how many variations a verb has
    tenses3 = [infinitive_pos, present_pos, pres_prog_pos]
    tenses4 = tenses3 + [past_pos]
    tenses5 = tenses4 + [past_prog_pos]

    verbs = set()

    for lemma in wn.all_lemma_names(pos='v'):
        if len(lemma) < min_length:
            continue
        if '_' in lemma:
            continue

        forms = lexeme(lemma)  # all possible conjugations of this verb (lemma)

        if len(forms) == 3:
            forms = zip(forms, tenses3)
        elif len(forms) == 4:
            forms = zip(forms, tenses4)
        elif len(forms) == 5:
            forms = zip(forms, tenses5)
        else:
            # this step can introduce errors, as getpostag isn't
            # guaranteed to return a verb tag
            forms = [(form, getpostag(form)) for form in forms]

        # ignore forms that do not map back to lemma by wordnet's
        # lemmatizer, as they are likely erroneous
        forms = list(filter(lambda form: lemma in wn._morphy(form[0], 'v'), forms))

        if tcm is not None:
            classes = [classy for syn in wn.synsets(lemma, 'v') for classy in tcm.predict(syn)]
        else:
            classes = [syn.name() for syn in wn.synsets(lemma, 'v')]

        for classy in classes:
            for form, postag in forms:
                if not postag:
                    log.warning("{} has POS==None".format(form))
                    continue
                if postag[0] == 'n':  # dirty hack to avoid inconsistency introduced by postagger
                    continue
                verbs.add((form, postag, classy))
                if "'" in form:  # remove ' (couldn't -> couldnt)
                    verbs.add((form.replace("'", ""), postag, classy))

    return verbs


def product(list_a, list_b):
    for a in list_a:
        for b in list_b:
            try:
                yield a + [b]
            except TypeError:
                yield [a, b]


def tally_chunk_tag(path, num_workers):
    def do_work(in_queue, out_list):
        postagger = BackoffTagger.from_pickle()
        blacklist = POSBlacklist()
        postagger.set_wordnet_instance(new_wordnet_instance())
        # postagger = SpacyTagger()

        i = 0
        while True:
            batch = in_queue.get()
            if len(batch) == 0:  # exit signal
                return

            result_buffer = []
            for password, count in batch:

                chunks = getchunks(password)
                try:
                    postagged_chunks = pos_tag(chunks, postagger, blacklist)
                except:
                    log.error("Error: {}".format(chunks))
                    raise

                result_buffer.append((postagged_chunks, count))
                i += 1

                if i % 100000 == 0:
                    process_id = multiprocessing.current_process()._identity[0]
                    log.info("Process {} has worked on {} passwords..."
                             .format(process_id, i))

            out_list.extend(result_buffer)

    manager = Manager()

    results = manager.list()
    work = manager.Queue(num_workers)

    # start for workers
    pool = []
    for i in range(num_workers):
        p = Process(target=do_work, args=(work, results))
        p.start()
        pool.append(p)

    passwords = tally(path).items()
    buff = []
    for password, count in passwords:
        buff.append((password, count))
        if len(buff) == 10000:
            work.put(buff)
            buff = []

    if len(buff): work.put(buff)
    for i in range(num_workers): work.put([])  # send exit signal

    for p in pool:
        p.join()

    return results


def increment_synset_count(tree, synset, count=1):
    """ Given  a  WordNetTree, increases the  count  (frequency)
    of a  synset (does not propagate to its ancestors). This
    method is more efficient than WordNetTree.increment_synset()
    as it uses WordNetTree.hashtable() to avoid searching.

    It's different  from increment_node() in that it  increments
    the counts of ALL nodes  matching a key. In fact, it divides
    the count by the number of nodes matching the key.
    increment_node() resolves  ambiguity using the ancestor path
    received as argument.
    """
    index = tree.index
    key = synset.name()

    if key in index:
        nodes = index[key]
        count = float(count) / len(nodes)
        for n in nodes:
            if n.has_children():
                n = n.find('s.' + n.key)
            n.increment_value(count, cumulative=False)


def fit_tree_cut_models(passwords, estimator, specificity, num_workers):
    def do_work(passwords, noun_results, verb_results):
        wn = new_wordnet_instance()

        grammar_tagger = GrammarTagger()
        tag_converter = TagsetConverter()
        noun_tree = IndexedWordNetTree('n', wordnet=wn)
        verb_tree = IndexedWordNetTree('v', wordnet=wn)

        for chunks, count in passwords:
            for string, pos in chunks:
                syn = synset(string, pos, wn, tag_converter)
                if syn and syn.pos() == 'n':
                    increment_synset_count(noun_tree, syn, count)
                elif syn and syn.pos() == 'v':
                    increment_synset_count(verb_tree, syn, count)

        noun_results.append(np.array([leaf.value for leaf in noun_tree.leaves()]))
        verb_results.append(np.array([leaf.value for leaf in verb_tree.leaves()]))

    manager = Manager()
    noun_results = manager.list()
    verb_results = manager.list()
    pool = []

    share = math.ceil(len(passwords) / num_workers)
    for i in range(num_workers):
        work = passwords[i * share:i * share + share]
        p = Process(target=do_work, args=(work, noun_results, verb_results))
        p.start()
        pool.append(p)

    for p in pool:
        p.join()

    noun_counts = np.sum(noun_results, 0)
    verb_counts = np.sum(verb_results, 0)

    noun_tree = IndexedWordNetTree('n')
    verb_tree = IndexedWordNetTree('v')

    for i, leaf in enumerate(noun_tree.leaves()):
        leaf.value = noun_counts[i]
    for i, leaf in enumerate(verb_tree.leaves()):
        leaf.value = verb_counts[i]

    noun_tree.updateCounts()
    verb_tree.updateCounts()

    tcm_n = TreeCutModel('n', estimator=estimator, specificity=specificity)
    tcm_n.fit_tree(noun_tree)

    tcm_v = TreeCutModel('v', estimator=estimator)
    tcm_v.fit_tree(verb_tree)

    return tcm_n, tcm_v


class MyManager(BaseManager): pass


def fit_grammar(passwords, tagtype, estimator, tcm_n, tcm_v, num_workers):
    def do_work(passwords, tcm_n, tcm_v, out_list):
        # a fresh instance of wordnet
        wordnet = new_wordnet_instance()

        results = []

        for chunks, count in passwords:
            X = []  # list of list of tuples. X[0] holds one tuple for
            # every different synset of chunks[0]

            for string, pos in chunks:
                syn = synset(string, pos, wordnet, tag_converter)
                synlist = [None]  # in case synset is None

                if syn is not None:  # abstract (generalize) synset
                    if syn.pos() == 'n':
                        synlist = tcm_n.predict(syn)
                    elif syn.pos() == 'v':
                        synlist = tcm_v.predict(syn)

                chunkset = []  # all semantic variations of this chunk
                for syn in set(synlist):
                    chunkset.append((string, pos, syn))
                X.append(chunkset)

            # navigate the cross-product of the chunksets
            if len(X) > 1:
                n_variations = reduce(lambda x, y: x * len(y), X, 1)
                count_ = count / n_variations
                for x in reduce(product, X):
                    results.append((x, count_))
            elif len(X) == 1:
                for x in X[0]:
                    results.append(([x], count))
            else:
                log.warning("Unable to feed chunks to grammar: {}".format(chunks))

        out_list.extend(results)
        # log.info("Results delivered.")

    grammar = Grammar(estimator=estimator, tagtype=tagtype)

    # feed grammar with the 'prior' vocabulary
    if estimator == 'laplace':
        postagger = BackoffTagger.from_pickle()
        grammar.add_vocabulary(noun_vocab(tcm_n, postagger, min_length=3))
        grammar.add_vocabulary(verb_vocab(tcm_v, postagger, min_length=2))

    if tagtype != 'pos':
        manager = Manager()
        results = manager.list()
        pool = []

        share = math.ceil(len(passwords) / num_workers)
        for i in range(num_workers):
            # progressively empty passwords to free memory
            # work = [passwords.pop() for i in range(min(share, len(passwords)))]
            work = passwords[i * share:i * share + share]
            p = Process(target=do_work, args=(work, tcm_n, tcm_v, results))
            p.start()
            pool.append(p)

        log.info("Pool has {} workers".format(len(pool)))

        del passwords[:]  # this atrocity is really necessary to free memory

        for p in pool:
            p.join()

        grammar.fit(results, num_workers=num_workers)
    else:
        # add null synset to every segment before passing to grammar
        for i in range(len(passwords)):
            x, count = passwords[i]
            x = [(word, pos, None) for word, pos in x]
            passwords[i] = (x, count)

        grammar.fit(passwords, num_workers=num_workers)

    return grammar


def train_grammar(password_file, outfolder, tagtype='backoff',
                  estimator='laplace', specificity=None, num_workers=2):
    """Train a semantic password model"""

    # Chunking and Part-of-Speech tagging

    log.info("Counting, chunking and POS tagging... ")

    with Timer("counting, chunking and POS tagging", log):
        passwords = tally_chunk_tag(password_file, num_workers)
    # print(passwords)

    # Train tree cut models

    log.info("Training tree cut models... ")

    with Timer("training tree cut models", log):
        if tagtype != 'pos':
            tcm_n, tcm_v = fit_tree_cut_models(passwords, estimator,
                                               specificity, num_workers)
        else:
            tcm_n = None
            tcm_v = None

    log.info("Training grammar...")

    with Timer("training grammar", log):
        grammar = fit_grammar(passwords, tagtype, estimator, tcm_n, tcm_v, num_workers)

    log.info("Persisting grammar")
    grammar.write_to_disk(outfolder)
    noun_filepath = os.path.join(outfolder, 'noun_treecut.pickle')
    verb_filepath = os.path.join(outfolder, 'verb_treecut.pickle')
    pickle.dump(tcm_n, open(noun_filepath, 'wb'), -1)
    pickle.dump(tcm_v, open(verb_filepath, 'wb'), -1)

    log.info("Done.")

    return grammar


def options():
    parser = argparse.ArgumentParser()
    parser.add_argument('passwords', nargs='?', default=sys.stdin,
                        type=argparse.FileType('r'), help='a password list')
    parser.add_argument('output_folder', help='a folder to store the grammar model')
    parser.add_argument('--estimator', default='mle', choices=['mle', 'laplace'])
    parser.add_argument('-a', '--abstraction', type=int, default=None,
                        help='Detail level of the grammar. An integer > 0 proportional to \
        the desired specificity.')
    parser.add_argument('-v', action='append_const', const=1, help="""
        verbose level (e.g., -vvv) """)
    parser.add_argument('--tagtype', default='backoff',
                        choices=['pos_semantic', 'pos', 'backoff', 'word'])
    parser.add_argument('-w', '--num_workers', type=int, default=2,
                        help="number of cores available for parallel work")
    parser.add_argument('-n', '--number_split', action='store_true')
    return parser.parse_args()
