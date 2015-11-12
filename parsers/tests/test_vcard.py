#!/usr/bin/env python3

from parsers import vcard
from parsed import mk_options, crlf
import unittest

multiline_tag='''NOTE:VERSION: 3.0\nUID: 277\nREV: 2011-06-02T13:25:40Z\nFN: Some text\n\r
 N: Our\;Dude\nTEL\;TYPE=CELL\,VOICE: +79213332211\nURL: http://www.li\r
 nkedin.com/profile?viewProfile=&key=3\r
'''

class TestVCard(unittest.TestCase):
    def _get_grammar(self):
        return vcard.grammar(vcard.VCardCtx(newline=crlf))

    def _parser(self, name, options):
        grammar = self._get_grammar()
        tested = grammar.registered_objects[name]['obj']
        return tested(options)

    def _test_wrap(self, rule_name, text, tail=None, options=None):
        grammar = self._get_grammar()
        tested = self._parser(rule_name, options or mk_options())
        data = text + (tail or 'something')
        res = tested.parse(data)
        #self.assertEqual
        print(res.position, len(text))

    def test_wraps(self):
        self._test_wrap('vcard.begin', 'BEGIN:VCARD')
        self._test_wrap('vcard.end', 'END:VCARD')

    def test_atag(self):
        data = (
            ('simple', "TEL;TYPE=CELL,VOICE:+79213332211\r\n"),
            ('multiline', multiline_tag),
        )
        options=mk_options(trace_depth=2, is_remember=True)
        for name, item in data:
            with self.subTest(name):
                self._test_wrap('vcard.atag', item, options=options)

if __name__ == '__main__':
    unittest.main()
