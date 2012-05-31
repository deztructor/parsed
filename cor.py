#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2012 Denis Zalevskiy
# Licensed under MIT License

import collections

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
