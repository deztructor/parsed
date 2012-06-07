parsed
======

Simple PEG parser builder written on Python.

There are many parser generators for python but each of 'em has IMO
some disadvantages: e.g. not suitable for stream processing, or does
not allow to track parsing and understand where it was failed, or does
not support mode w/o skipping whitespaces, or has ugly rules syntax,
or does not allow to attach semantic action in-place...

"Parsed" is inspired by "arpeggio"
(http://arpeggio.googlecode.com/). This parser generator is
interesting and there was the chance I'll start to use it but...
maybe I am too lazy to study the code and modify it to correspond my
needs or, most probably, it is interesting to write own parser...  so
I wrote One More parser generator.

Writing new grammar parsers
---------------------------

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
        result = parse(src)
        if result != nomatch:
            position, data = result

### Rules

#### Character matching rule

* against single char

        #single char, ignore by default
        @rule
        def is_A(): return char('A')

* against char from iterable

        #matches against LF or CR, on match by default returns
        #matched character
        @rule
        def vspace(): return char('\r\n')

* against predicate

        import string

        #boolean predicate to test a char for some condition
        def __is_punct(c): return c in string.punctuation

        #any char matching predicate, return a value by default
        @rule
        def is_punctuation(): return char(__is_punct)

#### Sequence

Matching sequence of rules, using operator '+':

        #hash symbol('#'), followed by any 'abcABC'
        @rule
        def hashed_abc(): return char('#') + 'abcABC'

#### Choice

Short circuiting 'OR':

        #hashed_abc from the example above OR any char from 'abc' set
        @rule
        def hashed_abc_or_abc(): return hashed_abc | 'abc'

#### Negation

        #any character except 'a'
        @rule
        def not_a(): return ~char('a')

#### Repetition

        #character 'a' repeated 1 or more times
        @rule
        def one_or_more_a(): return char('a')[1:]

        #character 'a' repeated 0 or more times
        @rule
        def zero_or_more_a(): return char('a')[0:]

        #character 'a' or its absence
        @rule
        def maybe_a(): return char('a')[0:1]

#### Lookahead

Lookahead can be expressed or negating (adding prefix '-' operator) a
rule or by appending rule to sequence using bitwise AND ('&') operator.

        #character 'a', matches only if followed by any character from 'abc'
        #set, do not consume the following character
        @rule
        def a_before_abc(): return char('a') + -char('abc')

        #the same as above, in this case lookahead match is always
        #excluded from parsing results
        @rule
        def also_a_before_abc(): return char('a') & char('abc')

#### Parsing (semantic) action

        #extract a list of characters from double quoted string
        #consisting from 'abc' characters
        @rule
        def dquoted_abc(): return '"' + char('abc')[1:] + '"' > first


        #compose 2 characters in string like "{CHAR1}&{CHAR2}" if first is
        #from 'abc' set and second - from 'def'. lambda should be enclosed in
        #braces because it has lowest precendence
        @rule
        def abc_def(): return char('abc') + 'def' > (lambda x: x[0] + '&' + x[1])

        #lookahead result can be also included in parsing results if
        #lookahead declared using prefix '-' but not binary '&'
        @rule
        def a_before_abc(): return char('a') + (-char('abc') > value)

#### Examples

All examples above can be run and tested by running `examples/readmy.py`

### Predefined rules

TODO

### Predefined constants

        nomatch #means rule is not matched

        empty #end of input (eof) or ignored result

TODO

### Predefined actions

        list2str #string from list

        first, second #first/second element of list

        nth(N) #returns action extracting Nth list element

        ignore #return empty constant

TODO

### Parsing options

Now there is only one parser debugging option avaiable -- 'is_trace',
if it is set to True, parsing process will be traced into stderr.

What's next?
------------

* add option to ignore whitespaces

* add Abstract Syntax Tree visualization

* parser optimization

* ?..
