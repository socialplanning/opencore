## Script (Python) "insufficient_privileges"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=
##title=Insufficient Privileges
##

from Products.CMFCore.utils import getToolByName
from Products.CMFPlone import PloneMessageFactory as _

portal = context.portal_url.getPortalObject()
referer = context.REQUEST.environ.get('HTTP_REFERER', 
                                      context.portal_url)

plone_utils = getToolByName(portal, 'plone_utils')
plone_utils.addPortalMessage(_('Insufficient Privileges'))

state.setNextAction('redirect_to:string:%s' % referer)

return state
