from AccessControl.SecurityInfo import ModuleSecurityInfo
from Products.CMFPlone.i18nl10n import utranslate
import zope.i18nmessageid
ModuleSecurityInfo('zope.i18nmessageid').declarePublic('MessageFactory')
ModuleSecurityInfo('Products.CMFPlone.i18nl10n').declarePublic('utranslate')
