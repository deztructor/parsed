#/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2012 Denis Zalevskiy
# Licensed under MIT License

from parser import *

def space(): return ' \n\r\t', ignore
def digit_dec() : return '0123456789', value
def anum(): return r1_inf(digit_dec), list2str
def sn(): return [space, anum], first
def snplus(): return r1_inf(sn)
def lpar(): return '(', ignore
def rpar() : return ')', ignore
def S0gt(): return r0_inf(space), ignore
def atom(): return seq(S0gt, anum), first
def atoms(): return r1_inf(atom)
def alist(): return seq(lpar, atoms, rpar), first

p = mk_parser(alist)
print p('( 1)')
