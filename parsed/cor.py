#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2012 Denis Zalevskiy
# Licensed under MIT License

import collections
import traceback
import sys
import time
import types

def is_iterable(v):
    return isinstance(v, collections.Iterable)

def is_function(v):
    return isinstance(v, types.FunctionType)

def const(self_name_, base = object, **attrs):
    if not '__repr__' in attrs:
        attrs['__repr__'] = lambda *args: self_name_
    return type(self_name_, (base,), attrs)()

def prop_map(prop_map_name_, **kwargs):
    res = type(prop_map_name_, (object,), {})
    [setattr(res, k, staticmethod(v) if is_function(v) else v) \
     for (k, v) in kwargs.items()]
    return res

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
    print >>sys.stderr, msg.format(*args, **kwargs)

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
        if len(args) and fn.__name__ == '__init__':
            pr = args[1:]
            name = args[0].__class__.__name__
        else:
            pr = args
            name = fn.__name__
        log("{}({})", name, printable_args(*pr, **kwargs))
        log.traceback()
        res = fn(*args, **kwargs)
        log("{} => {}", name, printable_args(res))
        return res

    wrapper.__name__ = fn.__name__
    wrapper.__doc__ = fn.__doc__
    wrapper.__dict__.update(fn.__dict__)
    return wrapper

def integers(start = 0):
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

def escape_str(s):
    return ''.join([escape(c) for c in s])

def wrap(wrapper, s):
    return ''.join([wrapper, s, wrapper])

class Options(object):
    def __init__(self, **kwargs):
        self.__options = kwargs

    def __getattr__(self, name):
        return self.__options[name]

    def __setattr__(self, name, value):
        if name.startswith('_Options__'):
            self.__dict__[name] = value
        else:
            value = staticmethod(value) if is_function(value) else value
            self.__options[name] = value

    def __dir__(self):
        return self.__options.keys()

    def update(self, src):
        return self.__options.update(src)

    def copy(self):
        return Options(**dict(self.__options))

    def __eq__(self, other):
        return isinstance(other, Options) \
            and self.__options == other.__options

    def __ne__(self, other):
        return  isinstance(other, Options) \
            and self.__options != other.__options

    def __repr__(self):
        return ', '.join(['='.join([n, repr(getattr(self, n))]) \
                          for n in dir(self)])

class Stopwatch(object):
    def __init__(self):
        self.reset()

    def reset(self):
        self.begin = self._now

    @property
    def _now(self):
        return time.time()

    @property
    def dt(self):
        return self._now - self.begin

def apply_on_graph(top, operation_accessor, child_accessor):
    class Dummy:
        pass
    def cookie_scope(node, attr_name):
        def on_enter():
            setattr(node, attr_name, True)
        def on_exit(*args):
            delattr(node, attr_name)
        return Scope(on_enter, on_exit)

    d = Dummy()
    cookie_name = '_tmp_op_' + str(id(d))

    def do(node):
        if hasattr(node, cookie_name):
            return None
        with cookie_scope(node, cookie_name):
            op = operation_accessor(node)
            return (op(), [do(x) for x in child_accessor(node)])

    with cookie_scope(top, cookie_name):
        op = operation_accessor(top)
        cc = child_accessor(top)
        return (op(), [do(x) for x in cc])


if __name__ == '__main__':
    o = Options(a = 1, b = 2)
    print dir(o)
    print o.a
    o.update(dict(d = 3))
    print dir(o)
