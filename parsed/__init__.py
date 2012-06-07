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
def eol(): return eof | vspace > ignore
@rule
def eof(): return char(empty) > ignore
@rule
def space(): return char(' \n\r\t') > ignore
@rule
def spaces(): return space[0:] > ignore
@rule
def any_char(): return ~eof > value
@rule
def digit_dec() : return char('0123456789') > value
@rule
def digit_hex() : return char('0123456789ABCDEFabcdef') > value

def __is_ascii(s): return s in string.ascii_letters
@rule
def ascii(): return char(__is_ascii) > value
@rule
def ascii_digit(): return ascii | digit_dec
