#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2012 Denis Zalevskiy
# Licensed under MIT License

from cor import const, nth, Options

nomatch = const('nomatch')
empty = const('empty')
end = const('end')

def ignore(*x): return empty
def value(x): return x
def first(x): return x[0]
second = nth(1)
third = nth(2)
def list2str(x): return ''.join(x)
def str_from(idx): return lambda x: list2str(x[idx])

def is_str(c):
    return isinstance(c, str) or isinstance(c, unicode) or c == empty

def mk_options(**kwargs):
    res = Options(is_trace = False, is_remember = True,
                  use_unicode = False, is_stat = False)
    res.update(kwargs)
    return res

default_options = mk_options()
