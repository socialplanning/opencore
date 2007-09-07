from Testing import ZopeTestCase
from zope.app.tests.placelesssetup import setUp, tearDown
from Products.Five import zcml
from Products.OpenPlans.utils import parseDepends, doc_file
import Products.Five
import Products.Five.site
import Products.wicked
#import Products.filter
import Products.Archetypes
import Products.Fate
import Products.OpenPlans
import Products.testing
import Products.CMFCore
import Products.ATContentTypes
import topp.featurelets
import Products.listen

def installConfiguredProducts():
    config, handler = parseDepends()

    def registerProduct(values):
        for pkg in values:
            ZopeTestCase.installProduct(pkg, 0)

    handler({'zrequired' : registerProduct,
             'required' : registerProduct,
             'optional' : registerProduct,
             })

