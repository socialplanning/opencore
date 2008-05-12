from zope.interface import alsoProvides
try:
    from zope.interface import noLongerProvides
except ImportError:
    from Products.Five.utilities.marker import erase as noLongerProvides

from opencore.testing.utility import mock_utility
