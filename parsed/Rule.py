#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2012 Denis Zalevskiy
# Licensed under MIT License

from Parse import *
from cor import is_iterable, Err, integers
from Common import *

inf = const('inf')

class Forward(object):
    def __init__(self, name):
        self.name = name

    def __call__(self, *args, **kwargs):
        return self.fn(*args, **kwargs)

class Rule(object):

    def __init__(self, data, name):
        self.data = data
        self.name = name
        self.__integers = integers()

    def __repr__(self):
        return ''.join([self.__class__.__name__,'(', repr(self.name), ')'])

    @property
    def _next_child_name(self):
        return '_'.join([self.name, str(self.__integers.next())])

    def __add__(self, other):
        if is_str(other):
            other = CharRule(other)
        return SeqRule((self.active, other), self._next_child_name)

    def __radd__(self, other):
        if is_str(other):
            other = CharRule(other)
        elif is_iterable(other):
            return other.__add__((self,))
        return SeqRule((other, self.active), self._next_child_name)

    def __or__(self, other):
        if is_str(other):
            other = CharRule(other)
        return ChoiceRule((self.active, other), self._next_child_name)

    def __ror__(self, other):
        if is_str(other):
            other = CharRule(other)
        return ChoiceRule((other, self.active), self._next_child_name)

    def __getitem__(self, k):
        if not isinstance(k, slice):
            raise Err("Supports only slices now")
        if not (k.step is None or k.step == 1):
            raise cor.Err("Can't handle step != 1")
        start, stop = k.start, k.stop
        r = (0 if start is None else start,
             inf if stop is None else stop)
        return RangeRule(self.active, r, self._next_child_name)

    def __gt__(self, action):
        return ActiveRule(self, action)

    def __neg__(self):
        return LookupRule(self, self.name)

    def __invert__(self):
        return NotRule(self, ''.join(['~', self.name]))

    def __call__(self):
        if hasattr(self, 'parser'):
            return self.parser

        self.parser = Forward(self.name)

        data = self.data
        if isinstance(data, Rule):
            data = data()
        elif not is_str(data) and is_iterable(data):
            data = [x() for x in data]
        parser = self.fn(self.name, data, self.action)
        self.parser.fn = parser
        self.parser = parser
        return parser

    @property
    def active(self):
        return ActiveRule(self, self.action)

class TopRule(Rule):
    def __init__(self, fn):
        super(TopRule, self).__init__(fn, fn.__name__)
        self.fn = self.__mk_parser
        self.action = ignore

    def __mk_parser(self, name, fn, action):
        parser = fn()
        parser.name = name
        return parser()

class SeqRule(Rule):
    def __init__(self, rules, name):
        super(SeqRule, self).__init__(rules, name)
        self.fn = match_seq
        self.action = value

    def __add__(self, other):
        if is_str(other):
            other = CharRule(other)
        return SeqRule(self.data + (other,), self.name)

    def __radd__(self, other):
        if is_str(other):
            other = CharRule(other)
        elif is_iterable(other):
            return other.__add__((self,))
        return SeqRule((other,) + self.data, self.name)

class ChoiceRule(Rule):
    def __init__(self, rules, name):
        super(ChoiceRule, self).__init__(rules, name)
        self.fn = match_any
        self.action = value

    def __or__(self, other):
        if is_str(other):
            other = CharRule(other)
        return ChoiceRule(self.data + (other,), self.name)

    def __ror__(self, other):
        if is_str(other):
            other = CharRule(other)
        return ChoiceRule((other,) + self.data, self.name)

class NotRule(Rule):
    def __init__(self, rule, name):
        super(NotRule, self).__init__(rule, name)
        self.fn = not_equal
        self.action = value

    def __invert__(self):
        return self.data

class CharRule(Rule):
    def __init__(self, c, name = None):
        if c == empty:
            if name is None:
                name = 'nomatch?'
            self.fn, self.action = match_symbol, ignore
        elif is_iterable(c):
            if len(c) == 1:
                if name is None:
                    name = ''.join(['chr("', c, '")'])
                self.fn, self.action = match_symbol, ignore
            else:
                if name is None:
                    name = ''.join(['any("', c, '")'])
                self.fn, self.action = match_iterable, value
        elif callable(c):
            if name is None:
                name = c.__name__
            self.fn, self.action = match_cond(c), value
            c = nomatch
        else:
            raise Err("Don't know how to make match from {}", c)
        super(CharRule, self).__init__(c, name)

class RangeRule(Rule):
    def __init__(self, rule, from_to, name):
        super(RangeRule, self).__init__(rule, name)
        self.action = value
        begin, end = from_to
        def err(): raise Err("Can't handle {} range", from_to)
        if not begin:
            if end == inf:
                self.fn = zero_more
            elif end == 1:
                self.fn = range_0_1
            else:
                err()
        elif begin == 1 and end == inf:
            self.fn = one_more
        else:
            err()

class LookupRule(Rule):
    def __init__(self, rule, name):
        super(LookupRule, self).__init__(rule, '_'.join(['fwd', name]))
        self.fn = fwd_lookup
        self.action = ignore

    def __neg__(self):
        return self

class ActiveRule(Rule):
    def __init__(self, rule, action):
        super(ActiveRule, self).__init__(rule.data, rule.name)
        if hasattr(rule, 'parser'):
            self.parser = rule.parser
        self.fn = rule.fn
        self.action = action

    @property
    def active(self):
        return self

    def __gt__(self, action):
        self.action = action
        return self
