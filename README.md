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

Matches character against single character, set of characters passed
in the string or predicate accepting character and returning True on
matching. Examples are:

* char('A') # matches against 'A', on match by default skips/ignores
        it

* char('\r\n') # matches against LF or CR, on match by default returns
        matched character

* against predicate

        import string
        def is_punct(c): return c in string.punctuation

        char(is_punct) # matches against predicate, on match by
        default returns the character
