#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2012 Denis Zalevskiy
# Licensed under MIT License

import cor
from cor import Err
from Common import *

is_parser_trace = True
debug_indent_level = 0
debug_indent_sym = '  '

def __indent_plus():
    global debug_indent_level
    debug_indent_level += 1

def __indent_minus(*args):
    global debug_indent_level
    debug_indent_level -= 1

debug_indent = cor.Scope(__indent_plus, __indent_minus)

def debug_print(msg, *args, **kwargs):
    global debug_indent_sym, debug_indent_level
    cor.log("{}{}", debug_indent_sym * debug_indent_level, \
            msg.format(*args, **kwargs))

def parser(name):
    def mk_name(name):
        return ''.join([name, '?'])
    def deco(fn):
        global is_parser_trace
        fn.__name__ = mk_name(name)
        def wrapper(src):
            global debug_indent
            pr = src if len(src) < 20 else ''.join([str(src[:20]), '...'])
            pr = cor.escape_str(pr)
            debug_print("{}({}) {{", fn.__name__, cor.wrap('"',pr))
            with debug_indent:
                res = fn(src)
            debug_print("}} => {}", cor.printable_args(res))
            return res
        if is_parser_trace:
            wrapper.__name__ = mk_name(name)
            return wrapper
        else:
            return fn
    return deco

class InfiniteInput(object):

    len_limit = 1024 * 64

    def __init__(self, src, begin = 0, end = None):
        self.__s = src
        self.__begin = begin
        self.__is_endless = end is None
        if end is None:
            self._end = lambda: len(src)
        else:
            self._end = lambda: end

    def __get_slice(self, k):
        start, stop = k.start, k.stop
        if not (k.step is None or k.step == 1):
            raise cor.Err("Can't handle step != 1")
        if start is None:
            start = self.__begin
        else:
            start = min(self.__begin + start, len(self.__s))
        if not stop is None:
            stop = min(self.__begin + stop, len(self.__s))
        return InfiniteInput(self.__s, start, stop)

    def __getitem__(self, i):
        if isinstance(i, slice):
            return self.__get_slice(i)
        end = self._end()
        i = self.__begin + i
        if i < end:
            return self.__s[i]
        elif i > self.len_limit:
            raise Exception("Length limit is reached")
        else:
            return nomatch

    def __str__(self):
        return str(self.__s[self.__begin:self._end()])

    def __repr__(self):
        return ''.join(['"', str(self), '"'])

    def __len__(self):
        return self._end() - self.__begin

    def __iter__(self):
        def gen():
            pos = 0
            while pos < len(self):
                yield self[pos]
                pos += 1
        return gen()

    def as_string(self):
        if isinstance(self.__s, str):
            if self.__begin == 0 and self.__is_endless:
                return self.__s
            elif self.__is_endless:
                return self.__s[self.__begin:]
            else:
                return self.__s[self.__begin:self._end()]
        else:
            res = [x for x in self.__s]
            res.append(chr(0))
            return ''.join(res)

def _match(name, s, conv):

    @parser(name)
    def cmp_sym(src):
        v = src[0]
        return (1, conv(v)) if v == s else nomatch

    @parser(name)
    def cmp_fn(src):
        v = src[0]
        return (1, conv(v)) if s(v) else nomatch

    if (is_str(s) or s == nomatch):
        return cmp_sym
    elif callable(s):
        return cmp_fn
    raise Err("Don't know how to match with {}", s)

def match_cond(c):
    return lambda name, dummy, action: _match(name, c, action)

def match_symbol(name, s, conv):
    if isinstance(s, str):
        if len(s) != 1:
            raise Err("{} len != 1", s)
    elif s != nomatch:
        raise Err("{} is not a string", s)
    return _match(name, s, conv)

def match_string(name, s, conv):
    if not isinstance(s, str):
        raise Err("{} is not a string", s)
    slen = len(s)
    @parser(name)
    def fn(src):
        if len(src) < slen:
            return nomatch
        v = src[0:slen].as_string()
        return (slen, conv(v)) if v == s else nomatch
    return fn

def match_iterable(name, pat, conv):
    if not cor.is_iterable(pat):
        raise Err("Don't know what to do with {}", seq)

    seq = [x for x in pat] if isinstance(pat, str) else pat
    @parser(name)
    def fn(src):
        v = src[0]
        return (1, conv(v)) if v in seq else nomatch
    return fn

def match_any(name, tests, conv):
    @parser(name)
    def fn(src):
        for test in tests:
            res = test(src)
            if res == nomatch:
                continue
            return (res[0], conv(res[1]))
        return nomatch
    return fn

def match_seq(name, tests, conv):
    @parser(name)
    def fn(src):
        total = []
        pos = 0
        for test in tests:
            res = test(src[pos:])
            if res == nomatch:
                return nomatch
            if res[1] != empty:
                total.append(res[1])
            pos += res[0]
        return pos, conv(total)
    return fn

def one_more(name, test, conv):
    @parser(name)
    def fn(src):
        total = []
        pos = 0
        res = test(src)
        if res == nomatch:
            return res
        while res != nomatch:
            data = res[1]
            if data != empty:
                total.append(data)
            pos += res[0]
            res = test(src[pos:])
        return pos, conv(total)
    return fn

def zero_more(name, test, conv):
    @parser(name)
    def fn(src):
        total = []
        pos = 0
        res = test(src)
        while res != nomatch:
            data = res[1]
            if data != empty:
                total.append(data)
            pos += res[0]
            res = test(src[pos:])
        return pos, conv(total)
    return fn

def range_0_1(name, test, conv):
    @parser(name)
    def fn(src):
        pos = 0
        res = test(src)
        if res == nomatch:
            return (0, conv(empty))
        else:
            data = res[1]
            if data != empty:
                data = conv(data)
            return (res[0], data)
    return fn

def not_equal(name, test, conv):
    @parser(name)
    def fn(src):
        res = test(src)
        return (1, conv(src[0])) if res == nomatch else nomatch
    return fn

def fwd_lookup(name, test, conv):
    @parser(name)
    def fn(src):
        res = test(src)
        return nomatch if res == nomatch else (0, conv(res[1]))
    return fn
