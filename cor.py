#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2012 Denis Zalevskiy
# Licensed under MIT License

import collections
import traceback

def is_iterable(v):
    return isinstance(v, collections.Iterable)

def const(name, base = object, **attrs):
    if not '__repr__' in attrs:
        attrs['__repr__'] = lambda *args: name
    return type(name, (base,), attrs)()

class Scope(object):
    def __init__(self, on_enter, on_exit):
        self.__on_enter = on_enter
        self.__on_exit = on_exit

    def __enter__(self):
        return self.__on_enter and self.__on_enter()

    def __exit__(self, *args):
        return self.__on_exit(*args) if self.__on_exit else False

class Null(object):

    def __init__(self, *args, **kwargs):
        self.__args = args
        [setattr(self, k, v) for k, v in kwargs.items()]

    def __getattr__(self, name):
        return lambda *args, **kwargs: Null()

    def __nonzero__(self):
        return False

    def __str__(self):
        return ''

    __repr__ = __str__

    def __call__(self, *args, **kwargs):
        return Null(*args, **kwargs)

class Err(Exception):
    def __init__(self, msg, *args, **kwargs):
        super(Err, self).__init__(msg.format(*args, **kwargs))

def log(msg, *args, **kwargs):
    print msg.format(*args, **kwargs)

def __traceback():
    t = traceback.format_exc().strip()
    if t and t != "None":
        log("TB:{}", t)

log.traceback = __traceback

def printable_args(*args, **kwargs):
    arglist = [repr(x) for x in args] \
        + ['='.join([repr(k), repr(v)]) for k, v in kwargs]
    return ', '.join(arglist)

def track(fn):
    def wrapper(*args, **kwargs):
        log("{}({})", fn.__name__, printable_args(*args, **kwargs))
        log.traceback()
        res = fn(*args, **kwargs)
        log("=> {}", printable_args(res))
        return res

    wrapper.__name__ = fn.__name__
    wrapper.__doc__ = fn.__doc__
    wrapper.__dict__.update(fn.__dict__)
    return wrapper

def integers(start):
    i = start
    while True:
        yield i
        i += 1

def nth(idx):
    res = lambda x: x[idx]
    res.__name__ = '_'.join(['nth', str(idx)])
    return res

__esc_data = (('"' ,  '"'), ( 'n' ,  '\n'),
              ( 'r' ,  '\r'), ('t', '\t'))
__escape = {k : v for v, k in __esc_data}
__unescape = {k : v for k, v in __esc_data}

def unescape(c):
    return __unescape[c] if (c in __unescape) else c

def escape(c):
    return ''.join(['\\', __escape[c]]) if (c in __escape) else c
