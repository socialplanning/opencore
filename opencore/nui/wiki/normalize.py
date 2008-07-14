#!/usr/bin/python
##########################################################
#
# Licensed under the terms of the GNU Public License
# (see docs/LICENSE.GPL)
#
# Copyright (c) 2005:
#   - The Plone Foundation (http://plone.org/foundation/)
#
##########################################################

#__authors__ = 'Anders Pearson <anders@columbia.edu>'
#__docformat__ = 'restructuredtext'

from unaccent import unaccented_map
import re
import types
import unittest

pattern1 = re.compile(r"^([^\.]+)\.(\w{,4})$")
pattern2 = re.compile(r'([\W\-]+)')
esc_char = re.compile(r'[~$]')
non_alpha = re.compile(r'[^a-zA-Z0-9~$]+')
u_esc = re.compile(r'\\u')
trailing_slash = re.compile(r"-+$")
leading_slash = re.compile(r"^-+")

def titleToNormalizedId(title="", umap=unaccented_map()):
    title = title.lower()
    title = title.strip()

    if title and isinstance(title, types.UnicodeType):
        title = title.translate(umap).encode("ascii", 'backslashreplace')
    base = title
    ext = ""
    m = pattern1.match(title)
    if m:
        base = m.groups()[0]
        ext = m.groups()[1]
    parts = pattern2.split(base)

    slug = base
    slug = slug.replace('~', '-')
    slug = slug.replace('\\u', '~')
    slug = slug.replace('\\U', '~U')
    slug = slug.replace('\\x', '~x')

    # replace non-alphanumeric characters with dashes
    slug = non_alpha.sub("-", slug)

    # trim slashes
    slug = leading_slash.sub("", slug)
    slug = trailing_slash.sub("", slug)
    if ext != "":
        slug = slug + "." + ext
    return slug


class NormTestCase(unittest.TestCase):
    tests = [
    (u"This is a normal title.", "this-is-a-normal-title"),
    (u"Short sentence. Big thoughts.", "short-sentence-big-thoughts"),
    (u"Some298374NUMBER", "some298374number"),
    (u'About folder.gif', u'about-folder.gif'),
    (u"laboratoire de g\xe9omatique", "laboratoire-de-geomatique"),
    (u'Eksempel \xe6\xf8\xe5 norsk \xc6\xd8\xc5', u'eksempel-aeoea-norsk-aeoea'), 
    (u'\u9ad8\u8054\u5408 Chinese', u'~9ad8~8054~5408-chinese'), 
    (u'\u30a2\u30ec\u30af\u30b5\u30f3\u30c0\u30fc\u3000\u30ea\u30df Japanese', u'~30a2~30ec~30af~30b5~30f3~30bf~30fc~3000~30ea~30df-japanese'), 
    (u'\uc774\ubbf8\uc9f1 Korean', u'~c774~bbf8~c9f1-korean'), 
    (u'\u0e2d\u0e40\u0e25\u0e47\u0e01\u0e0b\u0e32\u0e19\u0e40\u0e14\u0e2d\u0e23\u0e4c \u0e25\u0e35\u0e21 Thai',
     u'~0e2d~0e40~0e25~0e47~0e01~0e0b~0e32~0e19~0e40~0e14~0e2d~0e23~0e4c-~0e25~0e35~0e21-thai'),
    (u'fish & chips', u'fish-and-chips'),
    (u"~jim@work ", u"jimatwork")
    ]

    @classmethod
    def populate(cls):
        count = 0
        for ori, cor in cls.tests:
            count += 1
            setattr(cls, "test_%s" %count,  cls.make_test(ori, cor))
        return cls
    
    @classmethod        
    def make_test(cls, original, correct):
        def test_norming(self):
            sanitized = titleToNormalizedId(original)
            self.assertEqual(sanitized, correct)
        return test_norming
    
NormTestCase = NormTestCase.populate()

if __name__ == "__main__":
    unittest.main()




