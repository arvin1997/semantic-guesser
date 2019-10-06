import random

from context import score, pos, model
from pathlib import Path
from operator import itemgetter
import pickle
import time

grammar_path = Path('/Users/rafa/Data/grammar/yahoo-voices-laplace/')

postagger = pos.ExhaustiveTagger.from_pickle()
tc_nouns = pickle.load(open(grammar_path / 'noun_treecut.pickle', 'rb'))
tc_verbs = pickle.load(open(grammar_path / 'verb_treecut.pickle', 'rb'))
grammar = model.Grammar.from_files(str(grammar_path))

random.seed(123)

for k in range(10):
    N = 1000
    t1 = time.time()
    sample = sorted(grammar.sample(N), key=lambda x: x[1])

    matches = list(score.score((pwd[0] for pwd in sample),
                               grammar, tc_nouns, tc_verbs, postagger,
                               grammar.get_vocab()))

    num_wrong = 0
    for i, (pwd, base_struct, p) in enumerate(sample):

        password, matchlist = matches[i]

        maxp = 0
        try:
            for _, _base_struct, split, _p in sorted(matchlist, key=itemgetter(3), reverse=True):
                if pwd.islower() or \
                        pwd.isupper() or \
                        ''.join(map(str.capitalize, split)) == pwd or \
                        pwd[0].isupper() and pwd[1:].islower():
                    maxp = _p
                    break
        except:
            print(matchlist)
            raise

        if (p - maxp) > 1e-10:
            num_wrong += 1
            print(pwd, base_struct, p, _base_struct, _p)
    print("{}. Error rate: {} Time: {}s".format(k, num_wrong / N, time.time() - t1))
