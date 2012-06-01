#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2012 Denis Zalevskiy
# Licensed under MIT License

from cor import *

nomatch = Null()
empty = const('empty')
end = const('end')

def ignore(x): return empty
def value(x): return x
def first(x): return x[0]
second = nth(1)
def list2str(x): return ''.join(x)

is_parser_trace = True
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
    print debug_indent_sym * debug_indent_level, \
        msg.format(*args, **kwargs)

def parser(name):
    def deco(fn):
        global is_parser_trace
        fn.__name__ = name
        def wrapper(*args, **kwargs):
            global debug_indent
            debug_print("G:{}({}, {}) {{", fn.__name__, args, kwargs)
            with debug_indent:
                res = fn(*args, **kwargs)
            debug_print("}} => {}", res)
            return res
        if is_parser_trace:
            wrapper.__name__ = name
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
            self._end = lambda : len(src)
        elif callable(end):
            self._end = end
        else:
            self._end = lambda: end

    def __get_slice(self, k):
        start, stop = k.start, k.stop
        if not (k.step is None or k.step == 1):
            raise Err("Can't handle step != 1")
        start = self.__begin if start is None else self.__begin + start
        end = self._end if stop is None else self.__begin + stop
        return InfiniteInput(self.__s, start, end)

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
    def fn(src):
        v = src[0]
        return (1, conv(v)) if v == s else nomatch
    return fn

def _match_symbol(name, s, conv):
    if isinstance(s, str):
        if len(s) != 1:
            raise Exception("len != 1")
    elif s != nomatch:
        raise Exception("Not a string")
    return _match(name, s, conv)

def _match_string(name, s, conv):
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

def _match_iterable(name, pat, conv):
    if not is_iterable(pat):
        raise Exception("Don't know what to do with {}".format(seq))

    seq = [x for x in pat] if isinstance(pat, str) else pat
    @parser(name)
    def fn(src):
        v = src[0]
        return (1, conv(v)) if v in seq else nomatch
    return fn

def _match_any(name, tests, conv):
    @parser(name)
    def fn(src):
        for test in tests:
            res = test(src)
            if res == nomatch:
                continue
            return (res[0], conv(res[1]))
        return nomatch
    return fn

def _match_seq(name, tests, conv):
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

def _one_more(name, test, conv):
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

def _zero_more(name, test, conv):
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

def _0_1(name, test, conv):
    @parser(name)
    def fn(src):
        pos = 0
        res = test(src)
        return res[0], conv(res[1]) if res != nomatch else (0, empty)
    return fn

def _ne(name, test, conv):
    @parser(name)
    def fn(src):
        res = test(src)
        return (1, conv(src[0])) if res == nomatch else nomatch
    return fn

def is_str(c):
    return isinstance(c, str) or c == nomatch

class ParseInfo(tuple):
    def __new__(cls, *args):
        return tuple.__new__(cls, args)

def __mk_fn_parser(name, rule, action):
    fn, data = rule
    if not is_str(data):
        if is_iterable(data):
            data = [mk_parser(x) for x in data]
        else:
            data = mk_parser(data)
    return fn(name, data, action)

def __extract_rule(entity):
    if isinstance(entity, ParseInfo):
        return entity
    elif is_str(entity):
        return sym(entity)
    else:
        return nomatch

def __extract_rule_action(data, name = "?"):
    res = __extract_rule(data)
    if res != nomatch:
        return name, res, value
    elif is_iterable(data) and len(data) == 2:
        res = __extract_rule(data[0])
        if res != nomatch:
            return name, res, data[1]
    elif callable(data):
        return __extract_rule_action(data(), data.__name__)

    raise Err("Don't know how to extract from {}", data)

def __mk_parser(name, rule, action):
    if isinstance(rule, ParseInfo):
        return __mk_fn_parser(name, rule, action)

    raise Err("Do not know what to do with {}", rule)

def mk_parser(top, name = ""):
    return __mk_parser(*__extract_rule_action(top, name))

def r0_inf(test):
    return ParseInfo(_zero_more, test)
def r0_1(test):
    return ParseInfo(_0_1, test)
def r1_inf(test):
    return ParseInfo(_one_more, test)
def seq(*tests):
    return ParseInfo(_match_seq, tests)
def choice(*tests):
    return ParseInfo(_match_any, tests)
def ne(test):
    return ParseInfo(_ne, test)
def eof():
    return nomatch, ignore
def sym(c): return ParseInfo(_match_symbol, c) \
        if c == nomatch or len(c) == 1 \
        else ParseInfo(_match_iterable, c)
