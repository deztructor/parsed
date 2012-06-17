#/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2012 Denis Zalevskiy
# Licensed under MIT License

import string

import Rule
import Parse
from Common import *

def rule(fn): return Rule.TopRule(fn)

def char(c): return Rule.CharRule(c)
def text(s): return Rule.StringRule(s)

def source(src, begin = 0, end = None):
    return Parse.InfiniteInput(src, begin, end)

def cache_clean(rules_dict):
    '''rules_dict is ordinary result of grammar module globals()
    call'''
    for x in rules_dict.values():
        if isinstance(x, Rule.Rule):
            x.parser = None


@rule
def vspace(): return char('\n\r') > ignore
@rule
def hspace(): return char(' \t') > ignore
@rule
def crlf(): return text('\r\n') > ignore
@rule
def eol(): return eof | vspace > ignore
@rule
def eof(): return char(empty) > ignore
@rule
def space(): return char(' \n\r\t') > ignore
@rule
def spaces(): return space[0:] > ignore
@rule
def vspaces(): return vspace[0:] > ignore
@rule
def hspaces(): return hspace[0:] > ignore
@rule
def any_char(): return ~eof > value
@rule
def digit_dec() : return char('0123456789') > value
@rule
def digit_hex() : return char('0123456789ABCDEFabcdef') > value

@rule
def ascii():
    def __is_ascii(s): return s in string.ascii_letters
    return char(__is_ascii) > value
@rule
def ascii_digit(): return ascii | digit_dec

def within(begin, end):
    def check(c):
        i = ord(c)
        return i >= begin and i <= end
    @rule
    def fn():
        return char(check) > value
    return fn

@rule
def non_ascii():
    return within(0x80,0xff) > value

from datetime import datetime

@rule
def iso_date():
    return digit_dec[4]  + '-' + digit_dec[2] + '-' + digit_dec[2] + 'T' \
        + digit_dec[2] + ':' + digit_dec[2] + ':' + digit_dec[2] \
        + char('Z')[:1] \
        > (lambda x: datetime(*[int(list2str(i)) for i in x]))

@rule
def num_decimal(): return digit_dec[1:] & space \
    > (lambda x: int(list2str(x[0])))