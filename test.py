#/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2012 Denis Zalevskiy
# Licensed under MIT License

from parser import *

def vspace(): return '\n\r', ignore
def hspace(): return ' \t', ignore
def eol(): return choice(eof, vspace), ignore
def space(): return ' \n\r\t', ignore
def digit_dec() : return '0123456789', value
def anum(): return r1_inf(digit_dec), list2str
def sn(): return [space, anum], first
def snplus(): return r1_inf(sn)
def lpar(): return '(', ignore
def rpar() : return ')', ignore
def S0gt(): return r0_inf(space), ignore
def atom(): return seq(S0gt, anum), first
def semicol(): return ';', ignore
def noteol(): return ne(eol) 
def comment(): return seq(semicol, noteol, eol), first
def atoms(): return r1_inf(atom)
def alist(): return seq(lpar, atoms, rpar), first
def alist_or_comment(): return choice(comment, alist), value
def grammar(): return r0_inf(alist_or_comment), value

p = mk_parser(grammar)
print p(source('( 1);ee'))
