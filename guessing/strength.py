#!/usr/bin/env python

"""
Estimate strength as described in Dell'Amico and Filippone (2015)*.

* Dell'Amico, Matteo, and Maurizio Filippone.
  "Monte Carlo strength evaluation: Fast and reliable password checking."
  Proceedings of the 22nd ACM SIGSAC Conference on Computer and Communications Security.
  ACM, 2015.
"""

import argparse
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from guessing.score import score
from learning import model


def options():
    desc = """Estimate strength of each password in a list as described
    in Dell'Amico and Filippone (2015). Requires a password sample with
    pre-computed probabilities (see scorer.py).
    """

    epilog = """Example:

    scorer.py /path/to/mygrammar sample.txt > scored_sample.txt

    strength.py scored_sample.txt mygrammar passwords.txt"""

    # usage = "recognizer.py -p -g mygrammar sample.txt | strength.py mygrammar passwords.txt"

    parser = argparse.ArgumentParser(description=desc, epilog=epilog)
    parser.add_argument('sample',
                        type=argparse.FileType('r'),
                        help='a large and diverse list of passwords and their probabilities')
    parser.add_argument('--grammar',
                        help='grammar path for computing password probabilities.')
    parser.add_argument('--zeroes',
                        action='store_true',
                        help='if present, output passwords that have 0 p under the grammar')
    parser.add_argument('passwords',
                        nargs='?',
                        type=argparse.FileType('r'),
                        default=sys.stdin,
                        help='a list of passwords whose strength one wants to know. '
                             'Strength is defined as the number of guesses needed to crack the '
                             'password with the grammar used to estimate the sample\'s probabilities. '
                             'File is a space-delimited file with fields password, base structure, '
                             'and probability. If --grammar is set, then file is a list of '
                             'passwords.')
    parser.add_argument('-d', '--dedupe',
                        action="store_true",
                        help='drop duplicates in the sample. Default is False.')
    parser.add_argument('-m', '--multiplier',
                        type=int,
                        default=1,
                        help='a multiplier for the guess number estimate. Useful '
                             'for when each guess is modified by a number of mangling '
                             'rules.')

    return parser.parse_args()


def p_converter(x):
    try:
        return float(x)
    except:
        return None


def read_sample(f):
    return pd.read_csv(f,
                       sep='\t',
                       dtype={'password': object, 'p': np.float64},
                       converters={'p': p_converter},
                       names=['password', 'p'],
                       quoting=3)


def password_score_iterator(password_file, grammar_path):
    if grammar_path is None:
        for line in password_file:
            if line == '': break
            try:
                password, base_struct, p = line.rstrip().rsplit(maxsplit=2)
            except:
                sys.stderr.write("Malformed line:\n{}\n".format(line))
                continue
            yield (password, base_struct, float(p))
    else:
        grammar_dir = Path(grammar_path)

        tc_nouns = pickle.load(open(grammar_dir / 'noun_treecut.pickle', 'rb'))
        tc_verbs = pickle.load(open(grammar_dir / 'verb_treecut.pickle', 'rb'))
        grammar = model.Grammar.from_files(grammar_path)

        return score((line.lower().rstrip() for line in password_file),
                     grammar, tc_nouns, tc_verbs)


def main():
    opts = options()

    multiplier = opts.multiplier

    sample = read_sample(opts.sample)  # a pandas frame
    # drop duplicates
    if opts.dedupe:
        sample = sample.drop_duplicates("password")

    # load sample, sort it and compute cumulative probability
    sample = sample.sort_values('p', ascending=False)

    # compute the estimated number of passwords output before this one in a
    # process where the grammar's language is output in highest probability order
    # see Session 3.2 in Dell'Amico and Filippone (2015)
    n = len(sample)
    sample['strength'] = (1 / sample['p']).cumsum() * 1 / n

    # now sort it ascending, cause that's the only way binary search
    # will work in pandas (asc p is desc strength)
    sample = sample.sort_values('strength', ascending=False)

    # restore index
    sample = sample.reset_index().drop("index", axis=1)

    for password, struct, p in password_score_iterator(opts.passwords, opts.grammar):
        if p == 0:  # password isn't guessed by this grammar
            if opts.zeroes:
                sys.stdout.write("{}\t{:.2f}\n".format(password, 0))
            continue

        # find bisector (index where elements should be inserted to maintain order)
        # invert Dellamico's 3.2 instruction since our array is in ascending order
        bisector = sample['p'].searchsorted(p, side='left')[0]  # note left

        bisector = min(max(bisector + 1, 0), n - 1)  # index of the lowest prob. higher than p

        strength = sample['strength'][bisector] * multiplier

        sys.stdout.write("{}\t{:.2f}\n".format(password, strength))


if __name__ == '__main__':
    main()
