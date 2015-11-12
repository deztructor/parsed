#/usr/bin/env python

from parsers.vcard import grammar
import sys
from parsed import mk_options, nomatch

def extract(src):
    options = mk_options(trace_depth=0, is_remember=False)
    g = grammar(options=options)
    pos = 0
    prev_pos = -1
    res = []
    while pos < len(src):
        print('from ', pos)
        if prev_pos == pos:
            raise Exception('Stucked at the same pos?')
        prev_pos = pos
        print('---------------\n', src[pos:])
        pos, value = g.parse(src[pos:])
        if value == nomatch:
            break
        res.append(value)
    return res

if __name__ == '__main__':
    fname = sys.argv[1]
    with open(fname) as f:
        data = f.read()
    items = extract(data)
    print(len(items), items)
