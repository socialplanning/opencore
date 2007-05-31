## Controller Python Script "login_next"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind state=state
##bind subpath=traverse_subpath
##parameters=
##title=Login next actions
##

from Products.CMFPlone import PloneMessageFactory as _
from DateTime import DateTime
import ZTUtils

REQUEST = context.REQUEST

import pdb;  pdb.set_trace()

try:
    context.acl_users.credentials_cookie_auth.login()
except AttributeError:
    # The cookie plugin may not be used, or the site still uses GRUF
    pass

util = context.plone_utils
membership_tool=context.portal_membership
if membership_tool.isAnonymousUser():
    REQUEST.RESPONSE.expireCookie('__ac', path='/')
    util.addPortalMessage(_(u'Login failed'))
    return state.set(status='failure')

came_from = REQUEST.get('came_from', None)

# if we weren't called from something that set 'came_from' or if HTTP_REFERER
# is the 'logged_out' page, return the default 'login_success' form
if came_from is not None:
    scheme, location, path, parameters, query, fragment = util.urlparse(came_from)
    template_id = path.split('/')[-1]
    if template_id in ['login', 'login_success', 'login_password', 'login_failed',
                       'login_form', 'logged_in', 'logged_out', 'registered',
                       'mail_password', 'mail_password_form', 'join_form',
                       'require_login', 'member_search_results']:
        came_from = ''

    p_host = util.urlparse(context.portal_url())[1].split(":")[0]
    url_host = location.split(":")[0]
    if url_host and p_host != url_host:
        came_from = ''

js_enabled = REQUEST.get('js_enabled','1') != '0'
if came_from and js_enabled:
    # If javascript is not enabled, it is possible that cookies are not enabled.
    # If cookies aren't enabled, the redirect will log the user out, and confusion
    # may arise.  Redirect only if we know for sure that cookies are enabled.

    util.addPortalMessage(_(u'Welcome! You are now logged in.'))
    came_from = util.urlunparse((scheme, location, path, parameters, query, fragment))
    REQUEST.RESPONSE.redirect(came_from)

state.set(came_from=came_from)

return state
