#/usr/bin/python3
import re
import subprocess
import time
from argparse import ArgumentParser
from collections import Counter, namedtuple
from itertools import chain, count, groupby
from random import choice
from os.path import dirname, join
from sys import exit, stdin, stderr

re_fortunes = re.compile('(^|\n%).*?(?=$|\n%)', re.S)
re_words = re.compile('\\b\\w+\\b')
fortunes_path = join(dirname(__file__), 'fortunes-openbsd')

def word_count(content):
    matches = re_words.finditer(content)
    return Counter(map(lambda m: m[0].lower(), matches))

def read_fortunes(paths):
    fortunes = []
    for path in paths:
        with open(path) as fortunes_file:
            fortunes[-1:] = [''.join(k) for s, k in groupby(fortunes_file, lambda l: l.startswith('%')) if not s]
    return fortunes

def score_fortune(fortune_count, input_count, relevant_keys):
    # This is NOT a good textual comparison because it is based on absolute instead of relative occurance etc.
    return sum(abs(fortune_count[w] - input_count[w]) for w in relevant_keys)

def score_fortune_length(fortune_count, input_count, relevant_keys):
    # Slightly better, considers text lengths but only on ties.
    return (sum(abs(fortune_count[w] - input_count[w]) for w in relevant_keys), abs(len(fortune_count) - len(input_count)))

arguments = ArgumentParser(description='Find a fortune cookie matching some text')
arguments.add_argument('--debug', action='store_true', default=False, help='Enable performance and partial result debugging')
arguments.add_argument('--stdin', action='store_true', default=False, help='Read match text from stdin instead of analyzing the git HEAD')
arguments.add_argument('--words', dest='score', action='store_const', default=score_fortune, const=score_fortune_length, help='Best matching fortune is selected based on word counts')
arguments.add_argument('files', nargs='*', default=[fortunes_path])
arguments = arguments.parse_args()

SUPPRESS = ()
def time_me(msg=None, last_ts=[None]):
    if last_ts[0] is None:
        last_ts[0] = time.process_time()
        return
        
    new_time = time.process_time()
    delta, last_ts[0] = new_time - last_ts[0], new_time
    if msg is not SUPPRESS:
        print(msg or 'Time elapsed', delta, file=stderr)

if not arguments.debug:
    def time_me(*args):
        pass

time_me(SUPPRESS)
fortunes = read_fortunes(arguments.files)
time_me('Reading fortunes from files')

if arguments.debug:
    with open(fortunes_path) as fortunes_file:
        fortunes_src = fortunes_file.read()
        fortunes_cmp = list(re_fortunes.finditer(fortunes_src))

    time_me('Regex matching read')

    print('Loaded {} fortunes'.format(len(fortunes)))
    print('(Or {} with regex)'.format(len(fortunes_cmp)))

words = chain.from_iterable(map(re_words.finditer, fortunes))
words = Counter(map(lambda m: m[0], words))

Fortune = namedtuple('Fortune', 'fortune, words')
fortune_words = [Fortune(fortune, word_count(fortune)) for fortune in fortunes]

time_me('Counted words')

most_common = words.most_common(40)

if arguments.debug:
    time_me(SUPPRESS)
    words_cmp = word_count(fortunes_src)
    time_me('Counted words full regex')

    for match, count in most_common:
        print(match, ':', count, file=stderr)

git_status = subprocess.run(['git', 'show', '--format=%B', '-s', 'HEAD'], stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, encoding='utf-8')

if git_status.returncode != 0 and not arguments.debug:
    print('Failed to query git commit info', file=stderr)
    exit(1)
elif git_status.returncode != 0:
    print('Failed to query git commit info, falling back to stdin', file=stderr)
    input_count = word_count(stdin.read())
elif arguments.stdin:
    input_count = word_count(stdin.read())
else:
    input_count = word_count(git_status.stdout)

relevant_keys = set(input_count.keys()) - set(m[0] for m in most_common)
if arguments.debug:
    print('Relevant words for matching:', relevant_keys, file=stderr)

def minlist(iterable, key=lambda x: x):
    iterable = iter(iterable)
    try:
        first = next(iterable)
        min_key, mins = key(first), [first]
    except StopIteration:
        return []

    for n in iterable:
        n_key = key(n)
        if n_key > min_key:
            continue
        elif n_key == min_key:
            mins.append(n)
        else:
            min_key, mins = n_key, [n]

    return mins

time_me(SUPPRESS)
best = minlist(fortune_words, key=lambda f: arguments.score(f.words, input_count, relevant_keys))
time_me('Scoring all fortune cookies')

fortune = choice(best).fortune
if arguments.debug:
    for key in relevant_keys:
        fortune = re.sub('\\b{}\\b'.format(key), lambda match: '\033[01;32m{}\033[00m'.format(match[0]), fortune, flags=re.IGNORECASE)
print(fortune, end='')

