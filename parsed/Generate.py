#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2012 Denis Zalevskiy
# Licensed under MIT License

from Rules import *
from cor import is_iterable, Err, integers, track, log
from Common import *

inf = const('inf')

class Forward(object):
    def __init__(self, name):
        self.name = ''.join(['>', name])

    def _get_stat(self, cookie):
        return self.__rule._get_stat(cookie)

    def use(self, rule):
        self.__rule = rule

    def match(self, src):
        return self.__rule.match(src)

def mk_first_match_rule(c):
    if c == empty:
        cls = FirstEqualRule
    elif is_iterable(c):
        if len(c) == 1:
            cls = FirstEqualRule
        else:
            cls = FirstEqualAnyRule
    elif callable(c):
        cls = FirstEqualPredRule
        c = match_first_predicate(c)
    else:
        raise Err("Don't know how to make match from {}", c)
    return cls(c)

def mk_rule(src):
    if isinstance(src, Rule):
        return src
    if is_iterable(src):
        return mk_first_match_rule(src)
    raise Err("Can't make rule from {}", src)

def mk_rule_seq(r1, r2, name):
    r1 = mk_rule(r1)
    r2 = mk_rule(r2)
    return SeqRule((r1, r2), name)

def mk_rule_lookahead(r):
    r = mk_rule(r)
    return LookaheadRule(r, r.name)

def mk_rule_seq_lookahead(r1, r2, name):
    r1 = mk_rule(r1)
    r2 = mk_rule_lookahead(r2)
    return SeqRule((r1, r2), name)

def mk_rule_choice(r1, r2, name):
    r1 = mk_rule(r1)
    r2 = mk_rule(r2)
    return ChoiceRule((r1, r2), name)

def mk_rule_range(rule, from_to, name):
    begin, end = from_to
    def err(): raise Err("Can't handle {} range", from_to)
    if begin == inf or end == 0:
        err()

    if not begin:
        if end == inf:
            fn = zero_more
        elif end == 1:
            fn = range_0_1
        else:
            err()
    elif begin == 1 and end == inf:
        fn = one_more
    elif end != inf and begin <= end:
        fn = mk_closed_range(begin, end)
    else:
        err()

    return RangeRule(rule, fn, name)


class Rule(object):

    def __init__(self, name, action):
        self.name = name
        self.default_action = action
        self._action = None
        self.__integers = integers()
        self.__parser = None
        self.__options = None

    def __repr__(self):
        action_name = self.action.__name__ if self.action else ''
        return '{:s}({}, {})'.format(self.__class__.__name__,
                                     repr(self.name),
                                     repr(action_name))

    @property
    def _next_child_name(self):
        return '_'.join([self.name, str(self.__integers.next())])

    def __add__(self, other):
        return mk_rule_seq(self, other, self._next_child_name)

    def __radd__(self, other):
        if not is_str(other) and is_iterable(other):
            return other.__add__((self,))
        return mk_rule_seq(other, self, self._next_child_name)

    def __or__(self, other):
        return mk_rule_choice(self, other, self._next_child_name)

    def __ror__(self, other):
        return mk_rule_choice(other, self, self._next_child_name)

    def __and__(self, other):
        return mk_rule_seq_lookahead(self, other, self._next_child_name)

    def __rand__(self, other):
        return mk_rule_seq_lookahead(other, self, self._next_child_name)

    def __getitem__(self, k):
        if not isinstance(k, slice):
            return mk_rule_range(self, (k, k), self._next_child_name)

        if not (k.step is None or k.step == 1):
            raise cor.Err("Can't handle step != 1")
        start, stop = k.start, k.stop
        r = (0 if start is None else start,
             inf if stop is None else stop)
        return mk_rule_range(self, r, self._next_child_name)

    def __gt__(self, action):
        if action.__name__ == '<lambda>':
            action.__name__ = ''.join(['!', self.name])
        if isinstance(self, TopRule):
            return Converter(self, self.name, action)
        if self._action == action:
            return self
        self._action = action
        return self

    @property
    def action(self):
        return self._action if self._action else self.default_action

    def __neg__(self):
        return LookaheadRule(self, self.name)

    def __invert__(self):
        return NotRule(self, ''.join(['~', self.name]))

    @property
    def parser(self):
        return self.__parser

    def has_compatible_parser(self, options):
        return self.__parser and self.__options == options

    def __parser_declare(self, options):
        self.__options = options
        self.__parser = Forward(self.name)

    def __parser_define(self, parser):
        self.__parser.use(parser)
        self.__parser = parser

    def parser_cache_reset(self):
        self.__parser = None

    def __call__(self, options = default_options):
        if self.has_compatible_parser(options):
            return self.parser

        self.__parser_declare(options)
        parser = self.fn(self.name,
                         self._prepare_context(options),
                         self.action,
                         options)
        self.__parser_define(parser)
        return parser

class RuleWithData(Rule):

    def __init__(self, data, name, action):
        self.data = data
        super(RuleWithData, self).__init__(name, action)

    @property
    def copy(self):
        return self.__class__(self.data, self.name, self.default_action)

    def _prepare_context(self, options):
            return self.data

class Modifier(Rule):

    def __init__(self, rule, name, action):
        if not isinstance(rule, Rule):
            raise Err("{} should be rule", rule)
        self.rule = rule
        super(Modifier, self).__init__(name, action)

    @property
    def copy(self):
        return self.__class__(self.rule, self.name, self.default_action)

    def _prepare_context(self, options):
        return self.rule(options)

class Converter(Modifier):

    def __init__(self, rule, name, action):
        super(Converter, self).__init__(rule, name, action)
        self.fn = convert

class Aggregate(Rule):

    def __init__(self, rules, name, action):
        for rule in rules:
            if not isinstance(rule, Rule):
                raise Err("{} should be rule", rule)
        self.rules = rules
        super(Aggregate, self).__init__(name, action)

    @property
    def copy(self):
        return self.__class__(self.rules, self.name, self.default_action)

    def _prepare_context(self, options):
            return [x(options) for x in self.rules]

class TopRule(RuleWithData):
    def __init__(self, fn):
        super(TopRule, self).__init__(fn, fn.__name__, None)
        self.fn = self._mk_parser

    def _mk_parser(self, name, generator, action, options):
        rule = generator()
        rule.name = '.'.join([name, rule.name])
        parser = rule(options)
        return parser

    @property
    def copy(self):
        return self.__class__(self.data)

class SeqRule(Aggregate):
    def __init__(self, rules, name, action = value):
        super(SeqRule, self).__init__(rules, name, action)
        self.fn = match_seq

    def __add__(self, other):
        return SeqRule(self.rules + (mk_rule(other),), self.name)

    def __radd__(self, other):
        return SeqRule((mk_rule(other),) + self.rules, self.name)

    def __and__(self, other):
        other = mk_rule_lookahead(other)
        return SeqRule(self.rules + (other,), self.name)

    def __rand__(self, other):
        other = mk_rule_lookahead(other)
        return SeqRule((other,) + self.rules, self.name)

class ChoiceRule(Aggregate):
    def __init__(self, rules, name, action = value):
        for r in rules:
            r.default_action = value
        super(ChoiceRule, self).__init__(rules, name, action)
        self.fn = match_any

    def __or__(self, other):
        return ChoiceRule(self.rules + (mk_rule(other),), self.name)

    def __ror__(self, other):
        return ChoiceRule((mk_rule(other),) + self.rules, self.name)

class NotRule(Modifier):
    def __init__(self, rule, name, action = ignore):
        super(NotRule, self).__init__(rule, name, action)
        self.fn = not_equal

    def __invert__(self):
        return self.rule

class StringRule(RuleWithData):
    def __init__(self, s, name = None, action = value):
        if name is None:
            name = ''.join(['str("', s, '")'])
        self.fn = match_string
        super(StringRule, self).__init__(s, name, action)

class FirstEqualRule(RuleWithData):
    def __init__(self, c, name = None, action = None):
        if name is None:
            name = ''.join(['chr("', str(c), '")'])
        self.fn = match_first
        if action is None:
            action = ignore
        super(FirstEqualRule, self).__init__(c, name, action)

class FirstEqualAnyRule(RuleWithData):
    def __init__(self, c, name = None, action = None):
        if name is None:
            name = ''.join(['any("', str(c), '")'])
        self.fn = match_iterable
        if action is None:
            action = value
        super(FirstEqualAnyRule, self).__init__(c, name, action)

class FirstEqualPredRule(RuleWithData):
    def __init__(self, pred, name = None, action = None):
        if name is None:
            name = pred.__name__
        self.fn = pred
        if action is None:
            action = value
        super(FirstEqualPredRule, self).__init__(nomatch, name, action)

    @property
    def copy(self):
        return self.__class__(self.fn, self.name, self.default_action)

class FirstConsumeRule(RuleWithData):
    def __init__(self, action = None):
        self.fn = match_always
        if action is None:
            action = value
        super(FirstConsumeRule, self).__init__(nomatch, 'anything', action)

    @property
    def copy(self):
        return self.__class__(self.default_action)

class RangeRule(Modifier):
    def __init__(self, rule, fn, name):
        super(RangeRule, self).__init__(rule, name, value)
        self.fn = fn

    @property
    def copy(self):
        return self.__class__(self.rule, self.fn, self.name)

class LookaheadRule(Modifier):
    def __init__(self, rule, name, action = ignore):
        name = '_'.join(['fwd', name])
        super(LookaheadRule, self).__init__(rule, name, action)
        self.fn = lookahead

    def __neg__(self):
        return self
