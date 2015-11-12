#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2012 Denis Zalevskiy
# Licensed under MIT License

import unittest
from parsed import *
import parsed.Rules as Rules


class TestRulesGeneration(unittest.TestCase):

    def setUp(self):
        @rule
        def test_rule(): return char('1')
        self.char_generator = test_rule
        self.rule_name = 'test_rule.chr("1")?'

    def test_char_generator(self):
        r = self.char_generator(mk_options())
        self.assertIsInstance(r, Rules.Rule)
        self.assertEqual(r.name, self.rule_name)

        r2 = self.char_generator(mk_options(is_remember = False))
        self.assertIsNot(r2, r)
        self.assertEqual(r2.name, self.rule_name)
        self.assertIsInstance(r2, Rules.Rule)

    def test_generator_cache(self):
        r = self.char_generator(mk_options())
        r2 = self.char_generator(mk_options())
        self.assertIs(r, r2)

        self.char_generator.parser_cache_reset()
        r2 = self.char_generator(mk_options())
        self.assertIsNot(r, r2)

        r22 = self.char_generator(mk_options())
        self.assertIs(r22, r2)

        cache_clean(self.__dict__)

        r23 = self.char_generator(mk_options())
        self.assertIsNot(r23, r22)

        r3 = self.char_generator(mk_options(is_remember = False))
        self.assertIsNot(r3, r2)

        r4 = self.char_generator(mk_options(is_remember = False))
        self.assertIs(r4, r3)


class MatchTestBase(unittest.TestCase):

    def basic_match(self, gen, src, expected, options = mk_options()):
        r = gen(options)
        res = r.parse(src)
        self.assertEqual(res, expected)

class TestChar(MatchTestBase):

    def setUp(self):
        @rule
        def a(): return char('a') > (lambda x: 'A' + x)
        self.a = a

        @rule
        def b(): return char('b') > (lambda x: 'B' + x)
        self.b = b

        @rule
        def a2(): return a > (lambda x: 'a2' + x)
        self.a2 = a2

    def test_no_memoization(self):
        a = self.a()
        self.assertIsInstance(a, Rules.Rule)

    def test_match(self):
        self.basic_match(self.a, 'ab', (1, 'Aa'))

    def test_no_match(self):
        self.basic_match(self.a, 'ba', (0, nomatch))

    def test_derived(self):
        self.basic_match(self.a, 'ab', (1, 'Aa'))
        self.basic_match(self.a2, 'ab', (1, 'a2Aa'))

    def test_independent(self):
        self.basic_match(self.a, 'ab', (1, 'Aa'))
        self.basic_match(self.b, 'ba', (1, 'Bb'))


class TestPredicates(unittest.TestCase):

    def setUp(self):
        def pred(x): return x == 'x'
        @rule
        def a(): return char(pred) > (lambda x: 'a' + x)
        self.a = a

        @rule
        def a2(): return a > (lambda x: 'a2' + x)
        self.a2 = a2

    def test_memoization_default(self):
        a = self.a()
        self.assertIsInstance(a, Rules.CachingRule)

    def test_predicate(self):
        a = self.a()
        src = 'x'
        res = a.parse(src)
        self.assertEqual(res, (1, 'ax'))

    def test_derived(self):
        a = self.a()
        src = 'x'
        res = a.parse(src)
        self.assertEqual(res, (1, 'ax'))

        a2 = self.a2()
        res = a2.parse(src)
        self.assertEqual(res, (1, 'a2ax'))

class TestChoice(MatchTestBase):

    def setUp(self):
        @rule
        def a(): return char('a') > (lambda x: 'A' + x)
        @rule
        def b(): return char('b') > (lambda x: 'B' + x)
        @rule
        def c(): return a | b > (lambda x: 'c' + x)
        @rule
        def c1(): return c > (lambda x: 'c1' + x)
        @rule
        def c2(): return a | b | char('x') > (lambda x: 'c2' + x)

        self.c = c
        self.c1 = c1
        self.c2 = c2

    def test_memoization_default(self):
        c = self.c()
        self.assertIsInstance(c, Rules.CachingRule)

    def test_choice(self):
        self.basic_match(self.c, 'ab', (1, 'cAa'))

    def test_indep_rules(self):
        c = self.c()
        c2 = self.c2()
        self.assertNotEqual(c, c2)

        self.basic_match(self.c1, 'ab', (1, 'c1cAa'))
        self.basic_match(self.c1, 'ba', (1, 'c1cBb'))
        self.basic_match(self.c2, 'ab', (1, 'c2Aa'))
        self.basic_match(self.c2, 'xab', (1, 'c2x'))

class TestSeq(MatchTestBase):

    def setUp(self):
        @rule
        def a(): return char('a') > (lambda x: 'A' + x)
        @rule
        def b(): return char('b') > (lambda x: 'B' + x)
        @rule
        def c(): return a + b > value
        @rule
        def c1(): return c > (lambda x: x[0] + x[1])

        self.c = c
        self.c1 = c1

    def test_memoization_default(self):
        c = self.c()
        self.assertIsInstance(c, Rules.CachingRule)

    def test_seq(self):
        self.basic_match(self.c, 'ab', (2, ['Aa', 'Bb']))

    def test_indep_rules(self):
        c = self.c()
        c1 = self.c1()
        self.assertNotEqual(c, c1)

        self.basic_match(self.c1, 'ab', (2, 'AaBb'))

class TestRange(MatchTestBase):

    def setUp(self):
        @rule
        def a(): return char('a') > (lambda x: 'v' + x)
        @rule
        def b(): return a[0:] > (lambda x: ('x', x))

        self.a = a
        self.b = b

    def test_memoization_default(self):
        b = self.b()
        self.assertIsInstance(b, Rules.CachingRule)

    def test_0more(self):
        self.basic_match(self.b, 'aa', (2, ('x', ['va', 'va'])))

class TestComplex(MatchTestBase):

    def setUp(self):
        @rule
        def a(): return char('a') > (lambda x: 'A' + x)
        @rule
        def aplus(): return a[0:] > (lambda x: (len(x), x))
        @rule
        def c(): return char('c') > (lambda x: ('C', x))
        @rule
        def ac(): return c | aplus > (lambda x: ('AC', x))

        self.a = a
        self.aplus = aplus
        self.c = c
        self.ac = ac

    def test_ac(self):
        self.basic_match(self.ac, 'aa', (2, ('AC', (2, ['Aa', 'Aa']))))

class TestWithin(MatchTestBase):

    def setUp(self):
        @rule
        def a(): return within(ord('a'), ord('z')) > (lambda x: 'a' + x)
        self.a = a

    def test_memoization(self):
        a = self.a()
        self.assertIsInstance(a, Rules.CachingRule)

    def test_match(self):
        self.basic_match(self.a, 'bcd', (1, 'ab'))
        self.basic_match(self.a, 'cde', (1, 'ac'))
        self.basic_match(self.a, '-bcd', (0, nomatch))

class TestDefault(MatchTestBase):

    def test_vspace(self):
        self.basic_match(vspace, '\r', (1, empty))
        self.basic_match(vspace, '\n', (1, empty))
        self.basic_match(vspace, ' \n', (0, nomatch))
        self.basic_match(vspace, '\t\n', (0, nomatch))

    def test_hspace(self):
        self.basic_match(hspace, '\r ', (0, nomatch))
        self.basic_match(hspace, '\n', (0, nomatch))
        self.basic_match(hspace, ' \n', (1, empty))
        self.basic_match(hspace, '\t', (1, empty))

    def test_space(self):
        self.basic_match(space, '\r ', (1, empty))
        self.basic_match(hspace, '\t', (1, empty))

    def test_spaces(self):
        self.basic_match(spaces, '\r ', (2, empty))
        self.basic_match(spaces, '\t', (1, empty))
        self.basic_match(spaces, '\t\t\t', (3, empty))
        self.basic_match(spaces, '\t\r\n \t', (5, empty))
        self.basic_match(spaces, '-\t', (0, empty))


    def test_ascii(self):
        a = ascii(mk_options())
        pos, v = a.parse('ab')
        self.assertEqual(pos, 1)
        self.assertEqual(v, 'a')

        pos, v = a.parse('%')
        self.assertEqual(pos, 0)
        self.assertEqual(v, nomatch)

if __name__ == '__main__':
    unittest.main()

