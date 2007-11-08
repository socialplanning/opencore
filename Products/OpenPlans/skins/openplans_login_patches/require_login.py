## Script (Python) "require_login"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=
##title=Login
##

login = 'login'

from Products.CMFCore.utils import getToolByName
from Products.CMFPlone import PloneMessageFactory as _

portal = context.portal_url.getPortalObject()
# if cookie crumbler did a traverse instead of a redirect,
# this would be the way to get the value of came_from
#url = portal.getCurrentUrl()
#context.REQUEST.set('came_from', url)

if context.portal_membership.isAnonymousUser():
    plone_utils = getToolByName(portal, 'plone_utils')
    plone_utils.addPortalMessage(_(u'psm_please_sign_in', u'Please sign in to continue.'))
    referer = context.REQUEST.environ.get('HTTP_REFERER')
    if referer is not None:
        context.REQUEST.form['referer'] = referer
    return portal.restrictedTraverse(login)()
else:
    return portal.restrictedTraverse('insufficient_privileges')()

