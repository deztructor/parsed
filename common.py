#/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2012 Denis Zalevskiy
# Licensed under MIT License

import string

from rule import *

@rule
def vspace(): return char('\n\r') > ignore
@rule
def hspace(): return char(' \t') > ignore
@rule
def eol(): return eof | vspace > ignore
@rule
def eof(): return char(nomatch) > ignore
@rule
def space(): return char(' \n\r\t') > ignore
@rule
def spaces(): return space*(0,) > ignore
@rule
def any_char(): return ~eof > value
@rule
def digit_dec() : return char('0123456789') > value
@rule
def digit_hex() : return char('0123456789ABCDEFabcdef') > value

def __is_ascii(s): return s in string.ascii_letters
@rule
def ascii(): return char(__is_ascii) > value
