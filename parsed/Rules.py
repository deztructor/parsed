#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2012 Denis Zalevskiy
# Licensed under MIT License

from . import cor
from .cor import Err
from .Common import *

import collections
import functools

ParseResult = collections.namedtuple('ParseResult', 'position data')

class RuleMixin:

    def parse(self, src):
        self.cache_clear()
        return self.match(src, 0)

class Rule(cor.Registry, RuleMixin):

    def __init__(self, fn, name, options):
        super().__init__(name, fn=fn, options=options)
        if options.is_stat:
            self.__fn = fn
            self.match = self.__match_stat
            self.__stat = cor.Options(hits = 0, misses = 0)
        else:
            self.match = fn
        self.__name__ = name
        self._children = tuple()

    def __match_stat(self, src, pos):
        pos, value = self.__fn(src, pos)
        if value == nomatch:
            self.__stat.misses += 1
        else:
            self.__stat.hits += 1
        return pos, value

    def _get_stat(self):
        return (self.__name__, self.__stat)

    @property
    def stat(self):
        if not hasattr(self, '_Rule__stat'):
            return []
        return cor.apply_on_graph(self, lambda x: x._get_stat,
                                  lambda x: x.children)

    @property
    def children(self):
        return self._children

    @children.setter
    def children(self, v):
        self._children = v

    @property
    def name(self):
        return self.__name__

    def _cache_clear(self):
        pass

    def cache_clear(self):
        return cor.apply_on_graph(self, lambda x: x._cache_clear,
                                  lambda x: x.children)

class CachingRule(Rule):

    _cache_hits = 0

    def __init__(self, fn, name, options):
        self.__fn = fn
        super(CachingRule, self).__init__(self.__match, name, options)
        self.__cache = dict()

    def __match(self, src, pos):
        if pos in self.__cache:
            CachingRule._cache_hits += 1
            return self.__cache[pos]
        res = self.__fn(src, pos)
        self.__cache[pos] = res
        return res

    def _cache_clear(self):
        self.__cache = {}

class Tracer(RuleMixin):

    debug_indent_level = 0
    debug_indent_sym = ' ' * 2

    def __indent_plus(self):
        Tracer.debug_indent_level += 1

    def __indent_minus(self, *args):
        Tracer.debug_indent_level -= 1

    def debug_print(self, msg, *args, **kwargs):
        indent_level = Tracer.debug_indent_level
        if indent_level < self._max_depth:
            indent = Tracer.debug_indent_sym * indent_level
            cor.log("{}{}", indent, msg.format(*args, **kwargs))

    def __init__(self, rule, max_depth):
        self.__indent = cor.Scope(self.__indent_plus,
                                  self.__indent_minus)
        self.__rule = rule
        self.__name__ = rule.__name__
        self._max_depth = max_depth

    def match(self, src, pos):
        def tracable():
            dend = len(src) - pos
            pr = str(src[pos:]) if dend <= 20 \
                 else ''.join([str(src[pos:pos + 20]), '...'])
            pr = cor.escape_str(pr)
            return pr
        self.debug_print("{}({}) {{", self.__name__
                         , cor.wrap('"', cor.LazyPrintable(tracable)))
        with self.__indent:
            res = self.__rule.match(src, pos)
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

    def _cache_clear(self):
        return self.__rule.cache_clear()

def rule(name, options):
    def mk_name(name):
        return ''.join([name, '?'])

    def decorate(match_fn):
        cls = CachingRule if options.is_remember else Rule
        fn = cls(match_fn, mk_name(name), options)
        if options.trace_depth > 0:
            return Tracer(fn, options.trace_depth)
        else:
            return fn

    return decorate

#standard return if rule is not matched
_nomatch_res = ParseResult(0, nomatch)

def match_first_predicate(pred):
    def wrapper(name, dummy, action, options):
        @rule(name, options)
        def fn(src, pos):
            try:
                v = src[pos]
            except IndexError as e:
                v = empty
            if pred(v):
                v = action(v)
                return ParseResult(1, v) if v != nomatch else _nomatch_res
            else:
                return _nomatch_res
        return fn
    return wrapper

def match_first(name, s, action, options):
    if isinstance(s, str):
        if len(s) != 1:
            raise Err("{} len != 1", s)
    elif s != empty:
        raise Err("{} is not a string", s)

    custom_options = options.copy()
    custom_options.is_remember = False

    @rule(name, custom_options)
    def fn(src, pos):
        try:
            v = src[pos]
        except IndexError as e:
            v = empty
        if v != s:
            return _nomatch_res

        v = action(v)
        return ParseResult(1, v) if v != nomatch else _nomatch_res
    return fn

def match_string(name, s, action, options):
    if not isinstance(s, str):
        raise Err("{} is not a string", s)
    slen = len(s)
    @rule(name, options)
    def fn(src, pos):
        if len(src) - pos < slen:
            return _nomatch_res
        try:
            v = str(src[pos:pos + slen])
        except IndexError as e:
            return _nomatch_res
        return ParseResult(slen, action(v)) if v == s else _nomatch_res
    return fn

def match_iterable(name, pat, conv, options):
    if not cor.is_iterable(pat):
        raise Err("Don't know what to do with {}", seq)

    seq = [x for x in pat] if isinstance(pat, str) else pat
    @rule(name, options)
    def fn(src, pos):
        try:
            v = src[pos]
        except IndexError as e:
            v = empty
        if v in seq:
            v = conv(v)
            return ParseResult(1, v) if v != nomatch else _nomatch_res
        else:
            return _nomatch_res
    return fn

def match_any(name, tests, conv, options):
    @rule(name, options)
    def fn(src, pos):
        for test in tests:
            try:
                dpos, value = test.match(src, pos)
            except IndexError as e:
                return _nomatch_res

            if value != nomatch:
                value = conv(value)
                if (value != nomatch):
                    return ParseResult(dpos, value)
        return _nomatch_res
    fn.children = tests
    return fn

def match_always(name, dummy, action, options):
    @rule(name, options)
    def fn(src, pos):
        try:
            v = src[pos]
        except IndexError as e:
            v = empty
        v = action(v)
        return ParseResult(1, v) if v != nomatch else _nomatch_res
    return fn

def match_seq(name, tests, conv, options):
    @rule(name, options)
    def fn(src, spos):
        total = []
        pos = spos
        for test in tests:
            try:
                dpos, value = test.match(src, pos)
            except IndexError as e:
                dpos, value = _nomatch_res
            if value == nomatch:
                return _nomatch_res
            if value != empty:
                total.append(value)
            pos += dpos
        res = conv(total)
        return ParseResult(pos - spos, res) if res != nomatch else _nomatch_res
    fn.children = tests
    return fn

def one_more(name, test, conv, options):
    @rule(name, options)
    def fn(src, spos):
        total = []
        pos = spos
        try:
            dpos, value = test.match(src, pos)
        except IndexError as e:
            return _nomatch_res
        if value == nomatch:
            return _nomatch_res
        while value != nomatch:
            if value != empty:
                total.append(value)
            pos += dpos
            try:
                dpos, value = test.match(src, pos)
            except IndexError as e:
                dpos, value = 0, nomatch
        res = conv(total)
        return ParseResult(pos - spos, res) if res != nomatch else _nomatch_res
    fn.children = (test,)
    return fn

def mk_closed_range(begin, end):
    def closed_range(name, test, conv, options):
        @rule(name, options)
        def fn(src, spos):
            count = 0
            total = []
            pos = spos
            try:
                dpos, value = test.match(src, pos)
            except IndexError as e:
                dpos, value = _nomatch_res

            if value == nomatch:
                return _nomatch_res
            while value != nomatch:
                count += 1
                if count > end:
                    return _nomatch_res
                if value != empty:
                    total.append(value)
                pos += dpos
                try:
                    dpos, value = test.match(src, pos)
                except IndexError as e:
                    dpos, value = _nomatch_res
            if count >= begin:
                res = conv(total)
                return ParseResult(pos - spos, res) \
                    if res != nomatch \
                       else _nomatch_res
            else:
                return _nomatch_res

        fn.children = (test,)
        return fn
    return closed_range

def zero_more(name, test, conv, options):
    @rule(name, options)
    def fn(src, spos):
        total = []
        pos = spos
        try:
            dpos, value = test.match(src, pos)
        except IndexError as e:
            dpos, value = _nomatch_res

        while value != nomatch:
            if value != empty:
                total.append(value)
            pos += dpos
            try:
                dpos, value = test.match(src, pos)
            except IndexError as e:
                dpos, value = _nomatch_res
        res = conv(total)
        return ParseResult(pos - spos, res) \
            if res != nomatch \
               else _nomatch_res
    fn.children = (test,)
    return fn

def range_0_1(name, test, conv, options):
    @rule(name, options)
    def fn(src, spos):
        try:
            dpos, value = test.match(src, spos)
        except IndexError as e:
            dpos, value = _nomatch_res
        if value == nomatch:
            dpos, value = (0, empty)

        value = conv(value)
        return ParseResult(dpos, value) \
            if value != nomatch \
               else _nomatch_res
    fn.children = (test,)
    return fn

def not_equal(name, test, conv, options):
    @rule(name, options)
    def fn(src, spos):
        try:
            dpos, value = test.match(src, spos)
        except IndexError as e:
            dpos, value = _nomatch_res
        if value == nomatch:
            try:
                value = conv(src[spos])
            except IndexError as e:
                value = nomatch
            return ParseResult(0, value) \
                if value != nomatch \
                   else _nomatch_res
        else:
            return _nomatch_res
    fn.children = (test,)
    return fn

def convert(name, test, action, options):
    @rule(name, options)
    def fn(src, spos):
        try:
            dpos, value = test.match(src, spos)
        except IndexError as e:
            dpos, value = _nomatch_res
        if value != nomatch:
            value = action(value)
            return ParseResult(dpos, value) \
                if value != nomatch \
                   else _nomatch_res
        else:
            return _nomatch_res
    fn.children = (test,)
    return fn

def lookahead(name, test, conv, options):
    @rule(name, options)
    def fn(src, spos):
        try:
            dpos, value = test.match(src, spos)
        except IndexError as e:
            dpos, value = _nomatch_res
        if value != nomatch:
            value = conv(value)
            return ParseResult(0, value) \
                if value != nomatch \
                   else _nomatch_res
        else:
            return _nomatch_res
    fn.children = (test,)
    return fn
