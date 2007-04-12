from Products.CMFPlone.Portal import addPolicy
from Products.CMFPlone.interfaces.CustomizationPolicy import ICustomizationPolicy
from Products.CMFPlone.CustomizationPolicy import DefaultCustomizationPolicy
from Products.CMFCore.utils import getToolByName

def register(context, app_state):
    addPolicy('OpenPlans Site', OpenPlansSitePolicy())

class OpenPlansSitePolicy(DefaultCustomizationPolicy):
    """ Customizes the Plone site with full OpenPlans installation """
    __implements__ = ICustomizationPolicy

    availableAtConstruction = True
    
    def customize(self, portal):
        DefaultCustomizationPolicy().customize(portal)
        self.setupCMFMember(portal)
        self.setupOpenPlans(portal)

    def setupCMFMember(self, portal):
        portal.portal_quickinstaller.installProduct("CMFMember")
        portal.cmfmember_control.upgrade(swallow_errors=0) 
    
    def setupOpenPlans(self, portal):
        portal.portal_quickinstaller.installProduct("OpenPlans")
