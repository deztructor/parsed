#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2012 Denis Zalevskiy
# Licensed under MIT License

from parsed import *
from collections import namedtuple
from parsed.cor import Just, Nothing

import itertools

Tag = namedtuple('Tag', 'group name params value')
VCard = namedtuple('VCard', 'tags')

class VCardCtx:
    tag = Tag
    vcard = VCard

    def __init__(self, newline=Nothing):
        if newline:
            @rule
            def eol(): return eof | newline > ignore
            self._newline = newline
            self._eol = eol
            self.record_newline = newline
        else:
            @rule
            def record_newline():
                return text('\r\n') | text('\r\n') | '\r' | '\n' > self._set_crlf
            self.record_newline = record_newline
            self._newline = Nothing
            self._eol = Nothing

    def _set_crlf(self, x):
        self._eol = (text(x) > ignore)
        return empty

    @property
    def eol(self):
        return self._eol

    @property
    def newline(self):
        return self._newline

def grammar(ctx=None, options = mk_options(trace_depth=0)):

    rule = mk_rule('vcard')

    @rule
    def safe_char():
        return hspace | chr(0x21) | within(0x23, 0x2b) | \
            within(0x2d, 0x39) | within(0x3c, 0x7e) | non_ascii \
            > value

    @rule
    def qsafe_char():
        return hspace | chr(0x21) | within(0x23, 0x7e) | non_ascii \
            > value

    def wrap(name, value):
        @rule
        def delim():
            return text(name) + ':' + text(value) \
                > ignore
        return delim

    @rule
    def ne_end():
        return ~(text('END:') | text('BEGIN:')) + any_char > ignore

    @rule
    def iana_token(): return (ascii_digit | '-')[1:] > list2str

    @rule
    def x_name(): return text('X-') + iana_token > second

    @rule
    def name():
        return iana_token | x_name > value

    @rule
    def ptext(): return safe_char[0:] > list2str

    @rule
    def quoted_str(): return '"' + qsafe_char[0:] + '"' \
        > (lambda x: list2str(x[0]))

    @rule
    def param_value(): return ptext | quoted_str > value

    @rule
    def param_values():
        return param_value + (',' + param_value > first)[0:] \
            > (lambda x: (x[0], x[1]))

    @rule
    def tag_param(): return ';' + name + '=' + param_values \
        > value

    @rule
    def tag_name():
        return -ne_end + name > first

    @rule
    def text_begin():
        return (~ctx.eol + any_char > first)[1:] + ctx.newline > str_from(0)

    @rule
    def text_continue():
        return hspace + text_begin > first

    def full_text(x):
        return x[0] \
            if not len(x[1]) \
            else ''.join(itertools.chain((x[0],), x[1]))

    @rule
    def tag_text():
        return text_begin + text_continue[1:] > full_text

    @rule
    def tag_spec(): return (iso_date | num_decimal) + newline > first

    @rule
    def tag_value():
        return tag_text | tag_spec | text_begin > value

    @rule
    def group():
        return (iana_token + '.' > first)[:1] > empty2str

    @rule
    def atag():
        return group + tag_name + tag_param[0:] + ':' + tag_value \
            > (lambda x: ctx.tag(*x))

    @rule
    def tags(): return atag[0:]

    @rule
    def begin():
        return wrap('BEGIN', 'VCARD') + ctx.record_newline

    @rule
    def end(): return wrap('END', 'VCARD') + ctx.eol

    @rule
    def vcard():
        return vspaces + begin + tags + end \
            > (lambda x: ctx.vcard(x[0]))

    if ctx is None:
        ctx = VCardCtx()

    return vcard(options)
