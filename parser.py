#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2012 Denis Zalevskiy
# Licensed under MIT License

from cor import *

nomatch = const('nomatch')
empty = const('empty')
end = const('end')

def ignore(*x): return empty
def value(x): return x
def first(x): return x[0]
second = nth(1)
third = nth(2)
def list2str(x): return ''.join(x)

is_parser_trace = False
debug_indent_level = 0
debug_indent_sym = '  '

def __indent_plus():
    global debug_indent_level
    debug_indent_level += 1

def __indent_minus(*args):
    global debug_indent_level
    debug_indent_level -= 1

debug_indent = Scope(__indent_plus, __indent_minus)

def debug_print(msg, *args, **kwargs):
    global debug_indent_sym, debug_indent_level
    log("{}{}", debug_indent_sym * debug_indent_level, \
            msg.format(*args, **kwargs))

def parser(name):
    def mk_name(name):
        return ''.join(['?', name])
    def deco(fn):
        global is_parser_trace
        fn.__name__ = mk_name(name)
        def wrapper(src):
            global debug_indent
            pr = src if len(src) < 20 else ''.join([str(src[:20]), '...'])
            debug_print("{}({}) {{", fn.__name__, repr(pr))
            with debug_indent:
                res = fn(src)
            debug_print("}} => {}", printable_args(res))
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
            raise Err("Can't handle step != 1")
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
            pos = self.__begin
            while pos != self._end():
                yield self[pos]
                pos += 1
        return gen

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

def source(src, begin = 0, end = None):
    return InfiniteInput(src, begin, end)

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
            raise Exception("len != 1")
    elif s != nomatch:
        raise Exception("Not a string")
    return _match(name, s, conv)

def match_string(name, s, conv):
    if not isinstance(s, str):
        raise Exception("Not a string")
    slen = len(s)
    @parser(name)
    def fn(src):
        if len(src) < slen:
            return nomatch
        v = src[0:slen].as_string()
        return (slen, conv(v)) if v == s else nomatch
    return fn

def match_iterable(name, pat, conv):
    if not is_iterable(pat):
        raise Exception("Don't know what to do with {}".format(seq))

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
            total.append(res[1])
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
            total.append(res[1])
            pos += res[0]
            res = test(src[pos:])
        return pos, conv(total)
    return fn

def range_0_1(name, test, conv):
    @parser(name)
    def fn(src):
        pos = 0
        res = test(src)
        return (0, conv(empty)) if res == nomatch else (res[0], conv(res[1]))
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
        return nomatch if res == nomatch else (0, res[1])
    return fn

def is_str(c):
    return isinstance(c, str) or c == nomatch

class ParseInfo(object):
    def __init__(self, fn, data, action):
        self.fn = fn
        self.data = data
        self.action = action

    @property
    def name(self):
        return self.fn.__name__

    def __repr__(self):
        args = printable_args(self.fn, self.data, self.action)
        return ''.join(['ParseInfo(', args, ')'])

def __mk_fn_parser(cache, name, rule, action):
    if not isinstance(rule, ParseInfo):
        raise Err("Rule is not ParseInfo but {}", rule)
    fn, data = rule.fn, rule.data
    idx = integers()
    def mk_name():
        return '_'.join([name, str(idx.next())])

    if is_str(data):
        if not len(name):
            name = wrap('"', data)
    elif isinstance(data, ParseInfo):
        data = __mk_parser(data, cache, data.name)
    elif is_iterable(data):
        data = [__mk_parser(x, cache, mk_name()) for x in data]
    else:
        data = __mk_parser(data, cache, name)

    return fn(name, data, action)

def __extract_rule(entity):
    if isinstance(entity, ParseInfo):
        return entity
    elif is_str(entity):
        return sym(entity)
    else:
        return nomatch

def __extract_rule_action(data, name):
    res = __extract_rule(data)
    if res != nomatch:
        return name, res, res.action
    elif is_iterable(data) and len(data) == 2:
        res = __extract_rule(data[0])
        if res != nomatch:
            return name, res, data[1]
    elif callable(data):
        return None

    raise Err("Don't know how to extract from {}", data)

class Forward(object):
    def __init__(self):
        pass
    def __call__(self, *args, **kwargs):
        return self.fn(*args, **kwargs)

def __mk_parser(top, cache, name):
    extracted = __extract_rule_action(top, name)
    if extracted is None:
        if top in cache:
            return cache[top]
        f = Forward()
        cache[top] = f
        extracted = __extract_rule_action(top(), top.__name__)
        res = __mk_fn_parser(cache, *extracted)
        f.fn = res
        return res
    else:
        return __mk_fn_parser(cache, *extracted)


def mk_parser(top, name = ""):
    cache = {}
    return __mk_parser(top, cache, name)

def __normalize(v):
    if callable(v):
        return v
    if isinstance(v, ParseInfo):
        res = lambda: v
        res.__name__ = v.name
        return res
    if is_str(v):
        fn = lambda: (v, value)
        fn.__name__ = ''.join(('!', v))
        return fn
    raise Err("Don't know how to normalize {}", v)


def r0_inf(test):
    return ParseInfo(zero_more, __normalize(test), value)
def r0_1(test):
    return ParseInfo(range_0_1, __normalize(test), value)
def r1_inf(test):
    return ParseInfo(one_more, __normalize(test), value)
def seq(*tests):
    return ParseInfo(match_seq, tests, value)
def choice(*tests):
    return ParseInfo(match_any, tests, value)
def ne(test):
    return ParseInfo(not_equal, __normalize(test), value)
def eof():
    return nomatch, ignore
def sym(c):
    if c == nomatch:
        return ParseInfo(match_symbol, c, ignore)
    if is_iterable(c):
        if len(c) == 1:
            return ParseInfo(match_symbol, c, ignore)
        else:
            return ParseInfo(match_iterable, c, value)
    elif callable(c):
        return ParseInfo(match_cond(c), nomatch, value)
    raise Err("Don't know how to make sym match from {}", c)

def lookup(rule):
    def rule_fn():
        return ParseInfo(fwd_lookup, rule, ignore), ignore
    rule_fn.__name__ = '_'.join(['lookup', parser.__name__])
    return rule_fn
