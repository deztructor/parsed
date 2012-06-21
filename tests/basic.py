#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2012 Denis Zalevskiy
# Licensed under MIT License

from parsed.Rules import InfiniteInput
import unittest
from parsed import mk_options, rule, char, cache_clean
import parsed.Parse as P

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

    def test_char_generator(self):
        r = self.char_generator(mk_options())
        self.assertIsInstance(r, P.Parser)
        self.assertEqual(r.name, 'test_rule?')

        r2 = self.char_generator(mk_options(is_remember = False))
        self.assertIsNot(r2, r)
        self.assertEqual(r2.name, 'test_rule?')
        self.assertIsInstance(r2, P.Parser)

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

if __name__ == '__main__':
    unittest.main()

