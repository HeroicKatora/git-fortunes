#/usr/bin/python3
import re
import subprocess
import time
from argparse import ArgumentParser
from collections import Counter, namedtuple
from itertools import chain, count, groupby
from sys import exit, stdin, stderr

re_fortunes = re.compile('(^|\n%).*?(?=$|\n%)', re.S)
re_words = re.compile('\\b\\w+\\b')
fortunes_path = 'fortunes-openbsd'

def word_count(content):
    matches = re_words.finditer(content)
    return Counter(map(lambda m: m[0], matches))

def read_fortunes(paths):
    fortunes = []
    for path in paths:
        with open(path) as fortunes_file:
            fortunes[-1:] = ['\n'.join(k) for s, k in groupby(fortunes_file, lambda l: l.startswith('%')) if not s]
    return fortunes

arguments = ArgumentParser(description='Find a fortune cookie matching some text')
arguments.add_argument('--debug', action='store_true', default=False)
arguments.add_argument('files', nargs='*', default=['fortunes-openbsd'])
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

if arguments.debug:
    time_me(SUPPRESS)
    words_cmp = word_count(fortunes_src)
    time_me('Counted words full regex')

    for match, count in words.most_common(40):
        print(match, ':', count, file=stderr)

git_status = subprocess.run(['git', 'show', '--format=%B', '-s', 'HEAD'], stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, encoding='utf-8')

if git_status.returncode != 0 and not arguments.debug:
    print('Failed to query git commit info', file=stderr)
    exit(1)
elif git_status.returncode != 0:
    print('Failed to query git commit info, falling back to stdin', file=stderr)
    input_count = word_count(stdin.read())
else:
    input_count = word_count(git_status.stdout)

def score_fortune(fortune_count):
    # This is NOT a good textual comparison because it is based on absolute instead of relative occurance etc.
    return sum(abs(fortune_count[w] - c) for w, c in input_count.items())

best = min(fortune_words, key=lambda f: score_fortune(f.words))
print(best.fortune)
