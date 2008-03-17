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
import zope.i18nmessageid
from Products.CMFPlone.i18nl10n import utranslate
_ = zope.i18nmessageid.MessageFactory('opencore')


portal = context.portal_url.getPortalObject()
request = context.REQUEST

# if cookie crumbler did a traverse instead of a redirect,
# this would be the way to get the value of came_from
#url = portal.getCurrentUrl()
#context.REQUEST.set('came_from', url)

referer = request.environ.get('HTTP_REFERER')

if context.portal_membership.isAnonymousUser():
    plone_utils = getToolByName(portal, 'plone_utils')
    plone_utils.addPortalMessage(_(u'psm_please_sign_in', u'Please sign in to continue.'))
    if referer is not None:
        request.form['referer'] = referer
    return portal.restrictedTraverse(login)()
else:
    # We're already logged in.
    if request.form.get('came_from'):
        referer = referer or ''
        if request.form['came_from'].split('?')[0] == referer.split('?')[0]:
            # AFAICT, the HTTP referer and the came_from value are equal when
            # Flunc (and possibly other clients) update the referer on
            # every redirect, which causes an infinite redirect loop
            # in our login code.  Break the loop by redirecting
            # somewhere innocuous. Firefox doesn't seem to have this
            # problem, it sets the referer header to the URL before
            # the one that caused a redirect.
            #
            # To accomplish this, we need to clobber the request vars
            # that insufficient_privileges.cpy looks for.
            # - pw/slinkp
            request.form['came_from'] = ''
            request.environ['HTTP_REFERER'] = portal.absolute_url()
    return portal.restrictedTraverse('insufficient_privileges')()

