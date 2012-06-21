#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2012 Denis Zalevskiy
# Licensed under MIT License

from parsed.Parse import InfiniteInput
import unittest

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

if __name__ == '__main__':
    unittest.main()

