import unittest
from Testing.ZopeTestCase import ZopeDocFileSuite, ZopeTestCase
from zope.testing import doctest

optionflags = doctest.ELLIPSIS

def test_suite():
    from zope.interface import alsoProvides
    from zope.component import provideAdapter
    from zope.app.annotation.interfaces import IAttributeAnnotatable
    from zope.app.annotation.interfaces import IAnnotations
    from zope.app.annotation.attribute import AttributeAnnotations
    globs = locals()

    readme = ZopeDocFileSuite("README.txt",
                              optionflags=optionflags,
                              package='opencore.geolocation',
                              test_class=ZopeTestCase,
                              globs = globs,
                              )

    return unittest.TestSuite((readme,))
