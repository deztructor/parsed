#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2012 Denis Zalevskiy
# Licensed under MIT License

#import all definitions, it is better to declare any new grammar in
#the separate module
from parsed import *

#using to test and see how parser works
def test_parser(generator, src_str):
    parser = generator()
    print "Using", parser.__name__
    print "Parsing:", repr(src_str)
    src = source(src_str)
    print "GOT:", parser.parse(src)
    print

#basic parser generator function, on parsing tracking will be reported
#as 'abc?'
@rule
def abc(): return char('abc') > value

test_parser(abc, 'a')
test_parser(abc, 'e')


#### Character matching rules

#single char, ignore by default
@rule
def is_A(): return char('A')

test_parser(is_A, 'A')
test_parser(is_A, 'eA')

#any char from the sequence, return a value by default
@rule
def vspace(): return char('\r\n')

test_parser(vspace, '\n')
test_parser(vspace, ' ')

#boolean predicate to test a char for some condition
def __is_punct(c): return c in string.punctuation

#any char matching predicate, return a value by default
@rule
def is_punctuation(): return char(__is_punct)

test_parser(is_punctuation, ',')
test_parser(is_punctuation, 'W,')


#### Sequence

#hash symbol('#'), followed by any 'abcABC'
@rule
def hashed_abc(): return char('#') + 'abcABC'

test_parser(hashed_abc, '#B')
test_parser(hashed_abc, '#EC')
test_parser(hashed_abc, 'A')


#### Choice

#hashed_abc from the example above OR any char from 'abc' set
@rule
def hashed_abc_or_abc(): return hashed_abc | 'abc'

test_parser(hashed_abc_or_abc, '#BB')
test_parser(hashed_abc_or_abc, 'c')
test_parser(hashed_abc_or_abc, '#e')


#### Negation

#any character except 'a'
@rule
def not_a(): return ~char('a')

test_parser(not_a, 'ba')
test_parser(not_a, 'ab')


#### Repetition

#character 'a' repeated 1 or more times
@rule
def one_or_more_a(): return char('a')[1:]

test_parser(one_or_more_a, 'aaaba')
test_parser(one_or_more_a, 'abbaa')
test_parser(one_or_more_a, 'baaaa')

#character 'a' repeated 0 or more times
@rule
def zero_or_more_a(): return char('a')[0:]

test_parser(zero_or_more_a, 'baa')
test_parser(zero_or_more_a, 'aba')
test_parser(zero_or_more_a, 'aab')

#character 'a' or its absence
@rule
def maybe_a(): return char('a')[0:1]

test_parser(maybe_a, 'b')
test_parser(maybe_a, 'aa')


#### Lookahead

#character 'a', matches only if followed by any character from 'abc'
#set, do not consume the following character
@rule
def a_before_abc(): return char('a') + -char('abc')

#the same as above
@rule
def also_a_before_abc(): return char('a') & char('abc')

test_parser(a_before_abc, 'aa')
test_parser(also_a_before_abc, 'aa')

test_parser(a_before_abc, 'ab')
test_parser(also_a_before_abc, 'aa')



#### Parsing action

#extract a list of characters from double quoted string
#consisting from 'abc' characters
@rule
def dquoted_abc(): return '"' + char('abc')[1:] + '"' > first

test_parser(dquoted_abc, '"aabbcc"')
test_parser(dquoted_abc, '"bac"')
test_parser(dquoted_abc, 'abc')
test_parser(dquoted_abc, '"abc')

#compose 2 characters in string like "{CHAR1}&{CHAR2}" if first is
#from 'abc' set and second - from 'def'. lambda should be enclosed in
#braces because it has lowest precendence
@rule
def abc_def(): return char('abc') + 'def' > (lambda x: x[0] + '&' + x[1])

test_parser(abc_def, 'af')
test_parser(abc_def, 'ab')

#lookahead result can be also included in parsing results if
#lookahead declared using prefix '-' but not binary '&'
@rule
def a_before_abc(): return char('a') + (-char('abc') > value)

test_parser(a_before_abc, 'ab')
