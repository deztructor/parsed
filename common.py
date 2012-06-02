#/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2012 Denis Zalevskiy
# Licensed under MIT License

import string

from parser import *

def vspace(): return '\n\r', ignore
def hspace(): return ' \t', ignore
def eol(): return choice(eof, vspace), ignore
def space(): return ' \n\r\t', ignore
def spaces(): return r0_inf(space), ignore

def any_char(): return ne(eof), value
def digit_dec() : return '0123456789', value
def digit_hex() : return '0123456789ABCDEFabcdef', value
def ascii(): return sym(lambda s: s in string.ascii_letters), value
