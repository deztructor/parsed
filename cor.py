#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2012 Denis Zalevskiy
# Licensed under MIT License

import collections
import traceback

def is_iterable(v):
    return isinstance(v, collections.Iterable)

def const(name, base = object, **attrs):
    return type(name, (base,), attrs)

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

def track(fn):
    def wrapper(*args, **kwargs):
        arglist = [str(x) for x in args] \
            + ['='.join([str(k), str(v)]) for k, v in kwargs]
        log("{}({})", fn.__name__, ','.join(arglist))
        log.traceback()
        res = fn(*args, **kwargs)
        log("=> {}", res)
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
