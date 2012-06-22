#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2012 Denis Zalevskiy
# Licensed under MIT License

import cor
from cor import Err
from Common import *


class Rule(object):

    def __init__(self, fn, name):
        self.match = fn
        self.__name__ = name
        self.__children = tuple()

    @property
    def children(self):
        return self.__children

    @children.setter
    def children(self, v):
        self.__children = v

    @property
    def name(self):
        return self.__name__

    def parse(self, src):
        self.cache_clear()
        return self.match(src)

    def cache_clear(self):
        if len(self.children):
            [x.cache_clear() for x in self.children]

class CachingRule(Rule):

    _cache_hits = 0

    def __init__(self, fn, name):
        super(CachingRule, self).__init__(fn, name)
        self.__fn = self.match
        self.match = self.__match
        self.__cache = dict()

    def __match(self, src):
        apos = src.absolute_pos
        if apos in self.__cache:
            CachingRule._cache_hits += 1
            return self.__cache[apos]
        res = self.__fn(src)
        self.__cache[apos] = res
        return res

    def cache_clear(self):
        self.__cache = dict()
        if len(self.children):
            [x.cache_clear() for x in self.children]

class Tracer(object):

    debug_indent_level = 0
    debug_indent_sym = ' ' * 2

    def __indent_plus(self):
        Tracer.debug_indent_level += 1

    def __indent_minus(self, *args):
        Tracer.debug_indent_level -= 1

    def debug_print(self, msg, *args, **kwargs):
        indent = Tracer.debug_indent_sym * Tracer.debug_indent_level
        cor.log("{}{}", indent, msg.format(*args, **kwargs))

    def __init__(self, rule):
        self.__indent = cor.Scope(self.__indent_plus,
                                  self.__indent_minus)
        self.__rule = rule
        self.__name__ = rule.__name__

    def parse(self, src):
        return self.match(src)

    def match(self, src):
        pr = str(src) if len(src) < 20 else ''.join([str(src[:20]), '...'])
        pr = cor.escape_str(pr)
        self.debug_print("{}({}) {{", self.__name__, cor.wrap('"', pr))
        with self.__indent:
            res = self.__rule.match(src)
        self.debug_print("}} => {}", cor.printable_args(res))
        return res

    @property
    def children(self):
        return self.__rule.children

    @children.setter
    def children(self, v):
        self.__rule.children = v

    @property
    def name(self):
        return self.__name__

    def cache_clear(self):
        return self.__rule.cache_clear()


def rule(name, options):
    def mk_name(name):
        return ''.join([name, '?'])

    def decorate(match_fn):
        cls = CachingRule if options.is_remember else Rule
        fn = cls(match_fn, mk_name(name))
        if options.is_trace:
            return Tracer(fn)
        else:
            return fn

    return decorate

class InfiniteInput(object):
    '''imitates virtually infinite random access vector, returns empty
    after the end of source input
    '''

    len_limit = 1024 * 64

    def __init__(self, src, begin = 0, end = None):
        self.__s = src
        self.__begin = begin

        self.absolute_pos = src.absolute_pos + begin \
                            if hasattr(src, 'absolute_pos') \
                               else begin
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

    def __len__(self):
        return self._end() - self.__begin

    def __iter__(self):
        def gen():
            pos = 0
            while pos < len(self):
                yield self[pos]
                pos += 1
        return gen()

    def __str__(self):
        if isinstance(self.__s, str):
            if self.__begin == 0 and self.__is_endless:
                return self.__s
            elif self.__is_endless:
                return self.__s[self.__begin:]
            else:
                return self.__s[self.__begin:self._end()]
        else:
            res = [str(x) for x in self]
            return ''.join(res)

    def __repr__(self):
        return cor.wrap("'", str(self))


#standard return if rule is not matched
_nomatch_res = (0, nomatch)

def match_first_predicate(pred):
    def wrapper(name, dummy, action, options):
        @rule(name, options)
        def fn(src):
            v = src[0]
            if pred(v):
                v = action(v)
                return (1, v) if v != nomatch else _nomatch_res
            else:
                return _nomatch_res
        return fn
    return wrapper

def match_first(name, s, action, options):
    if isinstance(s, str) or isinstance(s, unicode):
        if len(s) != 1:
            raise Err("{} len != 1", s)
        if options.use_unicode:
            if isinstance(s, str):
                s = s.decode()
        else:
            if isinstance(s, unicode):
                s = s.encode()
    elif s != empty:
        raise Err("{} is not a string", s)

    custom_options = options.copy()
    custom_options.is_remember = False

    @rule(name, custom_options)
    def fn(src):
        v = src[0]
        if v != s:
            return _nomatch_res

        v = action(v)
        return (1, v) if v != nomatch else _nomatch_res

    return fn

def match_string(name, s, action, options):
    if not (isinstance(s, str) or isinstance(s, unicode)):
        raise Err("{} is not a string", s)
    if options.use_unicode:
        if isinstance(s, str):
            s = s.decode()
    else:
        if isinstance(s, unicode):
            s = s.encode()
    slen = len(s)
    @rule(name, options)
    def fn(src):
        if len(src) < slen:
            return _nomatch_res
        v = str(src[0:slen])
        return (slen, action(v)) if v == s else _nomatch_res
    return fn

def match_iterable(name, pat, conv, options):
    if not cor.is_iterable(pat):
        raise Err("Don't know what to do with {}", seq)

    seq = [x for x in pat] if isinstance(pat, str) else pat
    @rule(name, options)
    def fn(src):
        v = src[0]
        if v in seq:
            v = conv(v)
            return (1, v) if v != nomatch else _nomatch_res
        else:
            return _nomatch_res
    return fn

def match_any(name, tests, conv, options):
    @rule(name, options)
    def fn(src):
        for test in tests:
            pos, value = test.match(src)
            if value != nomatch:
                value = conv(value)
                if (value != nomatch):
                    return (pos, value)
        return _nomatch_res
    fn.children = tests
    return fn

def match_always(name, dummy, action, options):
    @rule(name, options)
    def fn(src):
        v = action(src[0])
        return (1, v) if v != nomatch else _nomatch_res
    return fn

def match_seq(name, tests, conv, options):
    @rule(name, options)
    def fn(src):
        total = []
        pos = 0
        for test in tests:
            dpos, value = test.match(src[pos:])
            if value == nomatch:
                return _nomatch_res
            if value != empty:
                total.append(value)
            pos += dpos
        res = conv(total)
        return (pos, res) if res != nomatch else _nomatch_res
    fn.children = tests
    return fn

def one_more(name, test, conv, options):
    @rule(name, options)
    def fn(src):
        total = []
        pos = 0
        dpos, value = test.match(src)
        if value == nomatch:
            return _nomatch_res
        while value != nomatch:
            if value != empty:
                total.append(value)
            pos += dpos
            dpos, value = test.match(src[pos:])
        res = conv(total)
        return (pos, res) if res != nomatch else _nomatch_res
    fn.children = list((test,))
    return fn

def mk_closed_range(begin, end):
    def closed_range(name, test, conv, options):
        @rule(name, options)
        def fn(src):
            count = 0
            total = []
            pos = 0
            dpos, value = test.match(src)
            if value == nomatch:
                return _nomatch_res
            while value != nomatch:
                count += 1
                if count > end:
                    return _nomatch_res
                if value != empty:
                    total.append(value)
                pos += dpos
                dpos, value = test.match(src[pos:])
            if count >= begin:
                res = conv(total)
                return (pos, res) if res != nomatch else _nomatch_res
            else:
                return _nomatch_res

        fn.children = list((test,))
        return fn
    return closed_range

def zero_more(name, test, conv, options):
    @rule(name, options)
    def fn(src):
        total = []
        pos = 0
        dpos, value = test.match(src)
        while value != nomatch:
            if value != empty:
                total.append(value)
            pos += dpos
            dpos, value = test.match(src[pos:])
        res = conv(total)
        return (pos, res) if res != nomatch else _nomatch_res
    fn.children = list((test,))
    return fn

def range_0_1(name, test, conv, options):
    @rule(name, options)
    def fn(src):
        pos, value = test.match(src)
        if value == nomatch:
            pos, value = (0, empty)

        value = conv(value)
        return (pos, value) if value != nomatch else _nomatch_res
    fn.children = list((test,))
    return fn

def not_equal(name, test, conv, options):
    @rule(name, options)
    def fn(src):
        if src[0] == empty:
            return _nomatch_res
        pos, value = test.match(src)
        if value == nomatch:
            value = conv(src[0])
            return (0, value) if value != nomatch else _nomatch_res
        else:
            return _nomatch_res
    fn.children = list((test,))
    return fn

def lookahead(name, test, conv, options):
    @rule(name, options)
    def fn(src):
        pos, value = test.match(src)
        if value != nomatch:
            value = conv(value)
            return (0, value) if value != nomatch else _nomatch_res
        else:
            return _nomatch_res
    fn.children = list((test,))
    return fn
