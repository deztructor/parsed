#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2012 Denis Zalevskiy
# Licensed under MIT License

from parsed import *
from parsed.cor import Err, log

def grammar(ctx):

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
            return vspaces + text(name) + ':' + text(value) + crlf \
                > ignore
        return delim

    @rule
    def ne_end():
        return ~(text('END:') | text('BEGIN:')) > ignore

    @rule
    def tag_name():
        return -ne_end + ascii[1:] > (lambda x: list2str(x[0]))

    @rule
    def iana_token(): return (ascii_digit | '-')[1:] > list2str

    @rule
    def x_name(): return text('X-') + iana_token > second

    @rule
    def param_name():
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
            > (lambda x: [x[0]] + x[1])

    @rule
    def tag_param(): return ';' + param_name + '=' + param_values \
        > value

    @rule
    def text_begin():
        return (~(crlf))[1:] + crlf > (lambda x: list2str(x[0]))

    @rule
    def text_continue():
        return hspace + text_begin > first

    def full_text(x):
        return x[0] if not len(x[1]) else ''.join([x[0]] + x[1])

    @rule
    def tag_text():
        return text_begin + text_continue[0:] > full_text

    @rule
    def tag_spec(): return (iso_date | num_decimal) + crlf > first
    
    @rule
    def tag_value():
        return tag_spec | tag_text > value

    @rule
    def atag():
        return vspaces + tag_name + tag_param[0:] + ':' + tag_value \
            > (lambda x: ctx.tag(x[0], x[1], x[2]))

    @rule
    def tags(): return atag[0:]

    @rule
    def vcard():
        return wrap('BEGIN', 'VCARD') + tags + wrap('END', 'VCARD') + eol

    return vcard(mk_options(is_trace = True))

class VCTag(object):
    def __init__(self, name, params, value):
        self.name = name
        self.params = dict(params)
        self.value = value

    def __repr__(self):
        return "VCTag({}, {}, {})".format(self.name, self.params, self.value)

    __str__ = __repr__

class VCard(object):
    def tag(self, name, params, value):
        return VCTag(name, params, value)


g = grammar(VCard())

vc = '''
BEGIN:VCARD\r
VERSION:3.0\r
EMAIL:Some_Name@somewhere.com\r
UID:e68dadab-3b36-4c05-94c8-29d037089014\r
N:Our;Dude;;;\r
NOTE:VERSION: 3.0\nUID: 277\nREV: 2011-06-02T13:25:40Z\nFN: Our Dude\n\r
 N: Our\;Dude\nTEL\;TYPE=CELL\,VOICE: +79213332211\nURL: http://www.li\r
 nkedin.com/profile?viewProfile=&key=3\r
TEL;TYPE=CELL,VOICE:+79213332211\r
REV:2012-05-15T21:14:20+03:00\r
URL:http://www.linkedin.com/profile?viewProfile=&key=3\r
EMAIL;TYPE=WORK:dude@nowhere.com\r
END:VCARD\r
'''

res = g(source(vc))

print res
