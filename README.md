parsed
======

Simple parser builder written on Python. Inspired by arpeggio parser
(http://arpeggio.googlecode.com/) but it was not suitable for my needs
and taste so it was simplier to write own parser generator.

Writing parsers
---------------

To create parser and use predefined rules one need to import parsed
package.

        from parsed import *

Parser generator function accepts no parameters and is decorated by
@rule, it should return a rule, e.g.:

        @rule
        def abc(): return char('abc') > value

As expected result of calling a generator function is a parser. Parser
gets its name from generator function name. This is why lambdas
etc. are not used. To correctly parse iterable source one should wrap
it with the source() function.

        parse = abc()
        src = source('a')
        position, result = parse(src)

### Rules

#### Character matching rule

* against single char

        #matches against 'A', on match by default skips/ignores it
        def is_A(): char('A')

* against char from iterable

        #matches against LF or CR, on match by default returns
        #matched character
        def vspace(): return char('\r\n')

* against predicate

        import string
        #predicate
        def __is_punct(c): return c in string.punctuation

        #matches against predicate, on match by default returns the
        #character
        def is_punctuation(): return char(__is_punct)

#### Sequence

Matching sequence of rules, using operator '+':

        # matches '#' followed by char matching to any character in
        # the 'abcABC' string
        @rule
        def hashed_abc(): return char('#') + 'abcABC'

#### Choice

Short circuiting 'OR':

        @rule
        def a_quote(): return hashed_abc | 'abc'

#### Negation

        @rule
        def not_a(): return ~char('a')

#### Repetition

        @rule
        def one_or_more_a(): return char('a')*(1,)

        @rule
        def zero_or_more_a(): return char('a')*(0,)

        @rule
        def maybe_a(): return char('a')*(0,1)

#### Forward lookup

        @rule
        def a_before_abc(): return char('a') + -char('abc')

#### Parsing action

        #extract a list of characters from double quoted string
        #consisting from 'abc' characters

        @rule
        def dquoted_abc(): return '"' + char('abc')*(1,) + '"' > first

        @rule
        def abc_def(): return char('abc') + 'def' > (lambda x: first + second)

