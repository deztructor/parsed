#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2012 Denis Zalevskiy
# Licensed under MIT License

from parsed.Rules import InfiniteInput
import unittest
from parsed import *
import parsed.Rules as Rules

class TestInfiniteInput(unittest.TestCase):

    def setUp(self):
        self.src = u'0123456789'
        self.tgt = InfiniteInput(self.src)

    def test_iter(self):
        a1 = [x for x in self.src]
        a2 = [x for x in self.tgt]
        self.assertEqual(a1, a2)

    def test_slice_iter(self):
        a1 = [x for x in self.src[:3]]
        a2 = [x for x in self.tgt[:3]]
        self.assertEqual(a1, a2)

        a1 = [x for x in self.src[1:2]]
        a2 = [x for x in self.tgt[1:2]]
        self.assertEqual(a1, a2)

        a1 = [x for x in self.src[1:]]
        a2 = [x for x in self.tgt[1:]]
        self.assertEqual(a1, a2)

    def test_str(self):
        a1 = str(self.src)
        a2 = str(self.tgt)
        self.assertEqual(a1, a2)

    def test_slice_str(self):
        a1 = str(self.src[:3])
        a2 = str(self.tgt[:3])
        self.assertEqual(a1, a2)

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

class TestChar(unittest.TestCase):

    def setUp(self):
        @rule
        def a(): return char('a') > (lambda x: 'a' + x)
        self.a = a

        @rule
        def b(): return char('b') > (lambda x: 'b' + x)
        self.b = b

        @rule
        def a2(): return a > (lambda x: 'a2' + x)
        self.a2 = a2

    def test_no_memoization(self):
        a = self.a()
        self.assertIsInstance(a, Rules.Rule)

    def test_match(self):
        a = self.a()

        pos, v = a.parse(source('ab'))
        self.assertEqual(pos, 1)
        self.assertEqual(v, 'aa')

    def test_no_match(self):
        a = self.a()

        pos, v = a.parse(source('ba'))
        self.assertEqual(pos, 0)
        self.assertEqual(v, nomatch)

    def test_derived(self):
        a = self.a()
        a2 = self.a2()

        pos, v = a.parse(source('ab'))
        self.assertEqual(pos, 1)
        self.assertEqual(v, 'aa')

        src = source('ab')
        pos, v = a2.parse(src)
        self.assertEqual(pos, 1)
        self.assertEqual(v, 'a2a')

    def test_independent(self):
        src = source('ab')
        a = self.a()
        res = a.parse(src)
        self.assertEqual(res, (1, 'aa'))

        b = self.b()
        src = source('ba')
        pos, v = b.parse(src)
        self.assertEqual(pos, 1)
        self.assertEqual(v, 'bb')

class TestBase(unittest.TestCase):

    def basic_match(self, gen, s, expected, options = mk_options()):
        r = gen(options)
        src = source(s)
        res = r.parse(src)
        self.assertEqual(res, expected)


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
        src = source('x')
        res = a.parse(src)
        self.assertEqual(res, (1, 'ax'))

    def test_derived(self):
        a = self.a()
        src = source('x')
        res = a.parse(src)
        self.assertEqual(res, (1, 'ax'))

        a2 = self.a2()
        res = a2.parse(src)
        self.assertEqual(res, (1, 'a2x'))

class TestChoice(TestBase):

    def setUp(self):
        @rule
        def a(): return char('a') > (lambda x: 'a' + x)
        @rule
        def b(): return char('b') > (lambda x: 'b' + x)
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
        self.basic_match(self.c, 'ab', (1, 'ca'))

    def test_indep_rules(self):
        c = self.c()
        c2 = self.c2()
        self.assertNotEqual(c, c2)

        self.basic_match(self.c1, 'ab', (1, 'c1a'))
        self.basic_match(self.c1, 'ba', (1, 'c1b'))
        self.basic_match(self.c2, 'ab', (1, 'c2a'))
        self.basic_match(self.c2, 'xab', (1, 'c2x'))

class TestWithin(TestBase):

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

class TestDefault(TestBase):

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
        pos, v = a.parse(source('ab'))
        self.assertEqual(pos, 1)
        self.assertEqual(v, 'a')

        pos, v = a.parse(source('%'))
        self.assertEqual(pos, 0)
        self.assertEqual(v, nomatch)

if __name__ == '__main__':
    unittest.main()

