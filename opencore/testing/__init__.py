from Products.OpenPlans.Extensions.create_test_content import create_test_content
from zope.interface import alsoProvides
try:
    from zope.interface import noLongerProvides
except ImportError:
    from Products.Five.utilities.marker import erase as noLongerProvides
