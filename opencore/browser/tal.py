# this will break in 2.10 and will need rewriting
from Products.Five.browser.metaconfigure import makeClassForTemplate
from Products.PageTemplates.Expressions import getEngine
from StringIO import StringIO
from zope.tal.talinterpreter import TALInterpreter
import unittest


def create_tal_context(view, **kw):
    data = dict(context=view.context,
                here=view.context,
                nothing=None,
                request=view.request,
                view=view)
    data.update(kw)
    return getEngine().getContext(data)

make_context = create_tal_context 

def render_tal(tal, context, macros={}, debug=0, stream=None):
    assert tal, """No tal was provided"""
    retval = False
    if stream is None:
        stream = StringIO(); retval = True
    ti = TALInterpreter(tal, macros, context, stream=stream, debug=debug)
    ti()
    if retval == True:
        return stream.getvalue()

render = render_tal 

def make_view_w_macro(tal, bases=(), name='template class', **cdict):
    """
    for testing purposes
    """
    import os
    import tempfile
    fd, filename = tempfile.mkstemp()
    fh = os.fdopen(fd, 'w')
    print >> fh, tal
    return makeClassForTemplate(filename, bases=bases, cdict=cdict, name=name)

def test_suite():
    from Testing.ZopeTestCase import ZopeTestCase
    from opencore.testing import dtfactory as dtf
    from pprint import pprint
    from zope.app.testing import placelesssetup
    from zope.component import Interface
    from zope.component import provideAdapter
    from zope.testing import doctest
    from zope.traversing.adapters import DefaultTraversable
    from zope.traversing.interfaces import ITraversable

    def setup(tc):
        provideAdapter(DefaultTraversable, adapts=(Interface,),  provides=ITraversable)

    tal_tests = dtf.ZopeDocFileSuite("tal.txt",
                                     package='opencore.browser',
                                     optionflags=doctest.ELLIPSIS,
                                     test_class=ZopeTestCase,
                                     setUp=setup,
                                     tearDown=placelesssetup.tearDown,
                                     
                                     globs=locals())
    return unittest.TestSuite((tal_tests,))

tests = test_suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
