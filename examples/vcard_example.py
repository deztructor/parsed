#/usr/bin/env python

from parsers.vcard import grammar

vcard_example_data = '''
BEGIN:VCARD\r
VERSION:3.0\r
EMAIL:Some_Name@somewhere.com\r
UID:e68dadab-3b36-4c05-94c8-29d037089014\r
N:Our;Dude;;;\r
NOTE:VERSION: 3.0\nUID: 277\nREV: 2011-06-02T13:25:40Z\nFN: Our Dude\n\r
 N: Our\;Dude\nTEL\;TYPE=CELL\,VOICE: +79213332211\nURL: http://www.li\r
 nkedin.com/profile?viewProfile=&key=3\r
TEL;TYPE=CELL,VOICE:+79213332211\r
EMAIL:pekka.Palomies@gmail.com\r
EMAIL:pekka.palomies@visfun.fi\r
TEL;TYPE=CELL,VOICE:+358504803092\r
ADR;TYPE=WORK:;;Palomiehentie 6;ESPOO;Uusimaa;02250;Finland\r
EMAIL;TYPE=WORK:pekka.palomies@espoo.com\r
EMAIL;TYPE=WORK:pekka.palomies@gmail.com\r
ADR;TYPE=HOME:;;Palomiehentie 6;ESPOO;Uusimaa;02250;Finland\r
EMAIL;TYPE=HOME:pekka.Palomies@gmail.com\r
TITLE:Engineer\, Deprecated SW\r
ORG:Anywhere\, D R&D\r
REV:2012-05-15T21:14:20+03:00\r
URL:http://www.linkedin.com/profile?viewProfile=&key=3\r
EMAIL;TYPE=WORK:dude@nowhere.com\r
END:VCARD\r
'''

def foo():
    g = grammar()
    print([k for k in g.registered_objects.keys() if k.startswith('vcard.be')])
    from parsed.Rules import CachingRule
    from parsed.cor import Stopwatch
    s = Stopwatch()
    pos, value = g.parse(vcard_example_data)
    print(s.dt, CachingRule._cache_hits)
    print(value)

if __name__ == '__main__':
    foo()
    #import cProfile
    #cProfile.run('foo()')

    #g.cache_clear()
