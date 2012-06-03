#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2012 Denis Zalevskiy
# Licensed under MIT License

from rule import *
from common import *
import cor

@rule
def sign(): return char('+-')*(0, 1) > \
        (lambda x: '+' if x == empty else x)
@rule
def atom_dec(): return sign + digit_dec*(1,) > \
        (lambda x: int(''.join([x[0], list2str(x[1])])))

@rule
def atom_hex(): return '#' + digit_hex*(1,) > \
        (lambda x: int(list2str(first(x)), 16))

@rule
def float10() : return digit_dec*(1,) + '.' + digit_dec*(0,) > value
@rule
def float01() : return digit_dec*(0,) + '.' + digit_dec*(1,) > value
@rule
def float_str(): return float10 | float01 > \
        (lambda x: '.'.join([list2str(x[0]), list2str(x[1])]))
@rule
def atom_float(): return sign + float_str > (lambda x: float(''.join(x)))

@rule
def number(): return atom_float | atom_dec | atom_hex > value
@rule
def escaped(): return '\\' + any_char > (lambda x: unescape(first(x)))
@rule
def str_chrs(): return (escaped | ~char('"'))*(0,) > list2str
@rule
def dquoted_str(): return '"' + str_chrs + '"' > first

@rule
def quoted(): return "'" + atom > (lambda x: ["'", x[0]])
@rule
def unit(): return number + '~' + name > (lambda x: [x[1], x[0]])

@rule
def atom_sym(): return ascii | "-./_:;*+=?!^%&|@$" > value
@rule
def name(): return atom_sym*(1,) > list2str
@rule
def keyword(): return ':' + name > value
@rule
def atom_body(): return keyword | unit | quoted | number | \
        name | dquoted_str | alist > value
@rule
def atom_end(): return space | ')' | ';' | eol > ignore
@rule
def atom(): return spaces + atom_body + -atom_end > first
@rule
def comment(): return ';' + ~eol*(0,) + eol >\
        (lambda x: list2str(x[0]))
@rule
def alist(): return '(' + (comment | atom)*(1,) + ')' > first
@rule
def grammar(): return comment | alist | atom > value


@rule
def t1(): return '#' | t2 > value
@rule
def t2(): return '%' | t1 > value


p = grammar()
s = source('(1 2;er\n#f "dd")')
print p(s)
