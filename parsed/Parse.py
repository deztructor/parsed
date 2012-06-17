#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2012 Denis Zalevskiy
# Licensed under MIT License

import cor
from cor import Err
from Common import *

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

def parser(name, options):
    def mk_name(name):
        return ''.join([name, '?'])

    def decorate(fn):
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

        if options.is_trace:
            wrapper.__name__ = mk_name(name)
            return wrapper
        else:
            return fn

    return decorate

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
            raise Err("Length limit is reached")
        else:
            return empty

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

#standard return if rule is not matched
_nomatch_res = (0, nomatch)

def _match(name, s, conv, options = default_options):

    @parser(name, options)
    def cmp_sym(src):
        v = src[0]
        if v == s:
            v = conv(v)
            return (1, v) if v != nomatch else _nomatch_res
        else:
            return _nomatch_res

    @parser(name, options)
    def cmp_fn(src):
        v = src[0]
        if s(v):
            v = conv(v)
            return (1, v) if v != nomatch else _nomatch_res
        else:
            return _nomatch_res

    if is_str(s):
        return cmp_sym
    elif callable(s):
        return cmp_fn
    raise Err("Don't know how to match with {}", s)

def match_cond(c):
    def gen(name, dummy, action, options = default_options):
        return  _match(name, c, action)
    return gen

def match_symbol(name, s, conv, options = default_options):
    if isinstance(s, str):
        if len(s) != 1:
            raise Err("{} len != 1", s)
    elif s != empty:
        raise Err("{} is not a string", s)
    return _match(name, s, conv, options)

def match_string(name, s, conv, options = default_options):
    if not isinstance(s, str):
        raise Err("{} is not a string", s)
    slen = len(s)
    @parser(name, options)
    def fn(src):
        if len(src) < slen:
            return _nomatch_res
        v = src[0:slen].as_string()
        if v == s:
            v = conv(v)
            return (slen, v) if v != nomatch else _nomatch_res
        else:
            return _nomatch_res
    return fn

def match_iterable(name, pat, conv, options = default_options):
    if not cor.is_iterable(pat):
        raise Err("Don't know what to do with {}", seq)

    seq = [x for x in pat] if isinstance(pat, str) else pat
    @parser(name, options)
    def fn(src):
        v = src[0]
        if v in seq:
            v = conv(v)
            return (1, v) if v != nomatch else _nomatch_res
        else:
            return _nomatch_res
    return fn

def match_any(name, tests, conv, options = default_options):
    @parser(name, options)
    def fn(src):
        for test in tests:
            pos, value = test(src)
            if value != nomatch:
                value = conv(value)
                if (value != nomatch):
                    return (pos, value)
        return _nomatch_res
    return fn

def match_seq(name, tests, conv, options = default_options):
    @parser(name, options)
    def fn(src):
        total = []
        pos = 0
        for test in tests:
            dpos, value = test(src[pos:])
            if value == nomatch:
                return _nomatch_res
            if value != empty:
                total.append(value)
            pos += dpos
        res = conv(total)
        return (pos, res) if res != nomatch else _nomatch_res
    return fn

def one_more(name, test, conv, options = default_options):
    @parser(name, options)
    def fn(src):
        total = []
        pos = 0
        dpos, value = test(src)
        if value == nomatch:
            return _nomatch_res
        while value != nomatch:
            if value != empty:
                total.append(value)
            pos += dpos
            dpos, value = test(src[pos:])
        res = conv(total)
        return (pos, res) if res != nomatch else _nomatch_res
    return fn

def mk_closed_range(begin, end):
    def closed_range(name, test, conv, options = default_options):
        @parser(name, options)
        def fn(src):
            count = 0
            total = []
            pos = 0
            dpos, value = test(src)
            if value == nomatch:
                return _nomatch_res
            while value != nomatch:
                count += 1
                if count > end:
                    return _nomatch_res
                if value != empty:
                    total.append(value)
                pos += dpos
                dpos, value = test(src[pos:])
            if count >= begin:
                res = conv(total)
                return (pos, res) if res != nomatch else _nomatch_res
            else:
                return _nomatch_res

        return fn
    return closed_range

def zero_more(name, test, conv, options = default_options):
    @parser(name, options)
    def fn(src):
        total = []
        pos = 0
        dpos, value = test(src)
        while value != nomatch:
            if value != empty:
                total.append(value)
            pos += dpos
            dpos, value = test(src[pos:])
        res = conv(total)
        return (pos, res) if res != nomatch else _nomatch_res
    return fn

def range_0_1(name, test, conv, options = default_options):
    @parser(name, options)
    def fn(src):
        pos, value = test(src)
        if value == nomatch:
            pos, value = (0, empty)

        value = conv(value)
        return (pos, value) if value != nomatch else _nomatch_res
    return fn

def not_equal(name, test, conv, options = default_options):
    @parser(name, options)
    def fn(src):
        if src[0] == empty:
            return _nomatch_res
        pos, value = test(src)
        if value == nomatch:
            value = conv(src[0])
            return (1, value) if value != nomatch else _nomatch_res
        else:
            return _nomatch_res
    return fn

def lookahead(name, test, conv, options = default_options):
    @parser(name, options)
    def fn(src):
        pos, value = test(src)
        if value != nomatch:
            value = conv(value)
            return (0, value) if value != nomatch else _nomatch_res
        else:
            return _nomatch_res
    return fn
