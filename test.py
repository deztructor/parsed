#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2012 Denis Zalevskiy
# Licensed under MIT License

from parser import *
from common import *
import cor

def sign(): return r0_1(choice(('+', value), ('-', value))),\
        lambda x: '+' if x == empty else x
def atom_dec(): return seq(sign, r1_inf(digit_dec)),\
        lambda x: int(''.join([x[0], list2str(x[1])]))
def atom_hex(): return seq('#', r1_inf(digit_hex)),\
        lambda x: int(list2str(first(x)), 16)

def float10() : return seq(r1_inf(digit_dec), '.', r0_inf(digit_dec)), value
def float01() : return seq(r0_inf(digit_dec), '.', r1_inf(digit_dec)), value
def float_str(): return choice(float10, float01), \
        lambda x: '.'.join([list2str(x[0]), list2str(x[1])])
def atom_float(): return seq(sign, float_str), lambda x: float(''.join(x))

def number(): return choice(atom_float, atom_dec, atom_hex), value

def atom_sym(): return choice(ascii, "-./_:;*+=?!^%&@$"), value
def name(): return r1_inf(atom_sym), list2str
def keyword(): return seq(':', name), value

def escaped(): return seq('\\', any_char), lambda x: unescape(first(x))
def str_chrs(): return r0_inf(choice(escaped, ne('"'))), list2str
def dquoted_str(): return seq('"', str_chrs, '"'), first

def quoted(): return seq("'", atom), lambda x: ["'", x[0]]
def unit(): return seq(number, '~', name), lambda x: [x[1], x[0]]

def atom_body(): return choice(keyword, unit, quoted, number, name,
                               dquoted_str, alist), value
def atom_end(): return choice(space, ')', eol), ignore
def atom(): return seq(spaces, atom_body, lookup(atom_end)), first
def comment(): return seq(';', r0_inf(ne(eol)), eol),\
        lambda x: list2str(x[0])
def alist(): return seq('(', r1_inf(atom), ')'), first
def alist_or_comment(): return choice(comment, alist, atom), value
def grammar(): return r0_inf(alist_or_comment), value

def test_str(): return seq(spaces, dquoted_str), first

p = mk_parser(alist_or_comment)
s = source('(34 ;ee\n-3 1 1.3 2 #f);ee')
pos = 0
while pos < len(s):
    res = p(s[pos:])
    if res == nomatch:
        break
    dpos, data = res
    pos += dpos
    print pos, data

#p2 = mk_parser(test_str)
#print p2(source(' "\e ter"'))
