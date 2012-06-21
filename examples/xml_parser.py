#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2012 Denis Zalevskiy
# Licensed under MIT License

from parsed import *
from parsed.cor import Err, log, prop_map
import sys
import codecs

def xml_parser(ctx, options = mk_options()):
    @rule
    def name_start_char():
            return ":" | within(ord('A'), ord('Z')) | "_" \
                | within(ord('a'), ord('z')) | within(0xC0, 0xD6) \
                | within(0xD8, 0xF6) | within(0xF8, 0x2FF) \
                | within(0x370, 0x37D) | within(0x37F, 0x1FFF) \
                | within(0x200C, 0x200D) | within(0x2070, 0x218F) \
                | within(0x2C00, 0x2FEF) | within(0x3001, 0xD7FF) \
                | within(0xF900, 0xFDCF) | within(0xFDF0, 0xFFFD) \
                | within(0x10000, 0xEFFFF) > value

    @rule
    def name_char():
        return name_start_char | "-" | "." | within(ord('0'), ord('9')) \
            | within(0xC2B7, 0xC2B7) | within(0x0300, 0x036F) \
            | within(0x203F, 0x2040) > value

    @rule
    def name():
        return name_start_char + name_char[0:] > \
            (lambda x: ctx.name(''.join([x[0], list2str(x[1])])))

    @rule
    def attr_end(): return ~ascii_digit > ignore
    @rule
    def attr_value(): return '"' + (~char('"'))[0:] + '"' \
        > (lambda x: list2str(x[0]))
    @rule
    def attribute():
        return spaces + name + spaces + '=' + spaces + attr_value & attr_end \
            > (lambda x: ctx.attr(*x))
    @rule
    def attributes(): return attribute[0:] + spaces > first
    @rule
    def stag(): return spaces + '<' + name + attributes \
            + (text('>') > ignore) > (lambda x: ctx.element(*x))
    @rule
    def etag(): return spaces + (text('</') > ignore) + name + '>' > first
    @rule
    def element(): return spaces + (empty_elem | n_empty_elem) + spaces > first
    @rule
    def xml_text(): return spaces + (~char('<'))[1:] > (lambda x: list2str(x[0]))
    @rule
    def child(): return element | comment | xml_text

    @rule
    def comment():
        return spaces + (text('<!--') > ignore) + (~text('-->'))[0:] \
            + (text('-->') > ignore) \
            > (lambda x: ctx.comment(list2str(x[0])))
    @rule
    def n_empty_elem(): return stag + child[0:] + etag > \
        (lambda x: ctx.element_close(*x))

    @rule
    def empty_elem():
        return '<' + name + attributes + (text('/>') > ignore) > \
            (lambda x: ctx.element(*x))
    @rule
    def pi():
        return spaces + (text('<?') > ignore) + (text('xml') | text('XML')) \
            + attributes + (text('?>') > ignore) \
            > (lambda x: ctx.proc_instr(*x))
    @rule
    def misc(): return comment | pi
    @rule
    def xml_decl(): return pi
    @rule
    def prolog(): return spaces + xml_decl + misc[0:]
    @rule
    def document(): return prolog + element + misc[0:] > \
        (lambda x: ctx.doc(x[0][0], x[0][1], x[1], x[2]))

    return document(options)


class XmlName(object):
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return self.name

    __str__ = __repr__

class XmlComment(object):
    def __init__(self, content):
        self.content = content

    def __repr__(self):
        return '<--{:s}-->'.format(self.content)

    __str__ = __repr__

class XmlDocument(object):
    def __init__(self, xml_decl, misc_begin, elem, misc_end):
        self.__decl = xml_decl
        self.__misc_begin = misc_begin
        self.__misc_end = misc_end
        self.__elem = elem

    def __repr__(self):
        return '{:s}\n{:s}\n{:s}\n{:s}'.format(
            self.__decl,
            '\n'.join(str(x) for x in self.__misc_begin),
            self.__elem,
            '\n'.join(str(x) for x in self.__misc_end))

    __str__ = __repr__

class XmlAttr(object):
    def __init__(self, name, value):
        self.name = name
        self.value = value

    def __repr__(self):
        return '='.join([str(self.name), repr(self.value)])

    __str__ = __repr__

class XmlElement(object):
    def __init__(self, name, attributes):
        self.name = name
        self.attributes = attributes
        self.children = []

    def __repr__(self):
        if len(self.attributes):
            if len(self.children):
                fmt = '<{name} {attrs}>\n{children}\n</{name}>'
            else:
                fmt = '<{name} {attrs}/>'
        elif len(self.children):
                fmt = '<{name}>\n{children}\n</{name}>'
        else:
            fmt = '<{name}/>'
        return fmt.format(name = self.name,
                          children = '\n'.join([str(x) for x in self.children]),
                          attrs = ' '.join([str(x) for x in self.attributes]))

    __str__ = __repr__

class XmlProcInstr(object):
    def __init__(self, name, attributes):
        self.name = name
        self.attributes = attributes

    def __repr__(self):
        if len(self.attributes):
            fmt = '<?{name} {attrs}?>'
        else:
            fmt = '<?{name}?>'
        return fmt.format(name = self.name,
                          attrs = ' '.join([str(x) for x in self.attributes]))

    __str__ = __repr__

def element_close(elem, children, closing):
    if str(elem.name) != str(closing):
        raise Err("Element {} but closed with {}", elem.name, closing)
    [elem.children.append(d) for d in children]
    return elem

xml_gen = prop_map('xmlgen',
                   doc = XmlDocument,
                   name = XmlName,
                   attr = XmlAttr,
                   element = XmlElement,
                   proc_instr = XmlProcInstr,
                   comment = XmlComment,
                   element_close = element_close)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        log("Call {} <svg file path>\n", sys.argv[0])
        exit(1)

    import parsed.cor as cor
    sw = cor.Stopwatch()
    p = xml_parser(xml_gen, mk_options(is_trace = False,
                                       is_remember = True,
                                       use_unicode = True))
    print sw.dt


    from parsed.Rules import CachingRule

    with codecs.open(sys.argv[1], encoding = 'utf-8') as f:
        s = u'\n'.join(f.readlines())
    s = source(s)

    sw.reset()
    res = p.parse(s)
    print sw.dt, CachingRule._cache_hits
    print res
