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
import zope.i18nmessageid
from Products.CMFPlone.i18nl10n import utranslate
_ = zope.i18nmessageid.MessageFactory('opencore')

portal = context.portal_url.getPortalObject()
dummy_referer = context.portal_url()
request = context.REQUEST
referer = request.environ.get('HTTP_REFERER', dummy_referer)
came_from = request.form.get('came_from', '')

#XXX This should all be refactored!
#XXX maybe put this in a view somewhere

# XXX you can't import things in skins :(
def query_dict(string):

    # XXX reinvent urllib.splitquery
    query = string.split('?')
    if len(query) != 2:
        return None

    # XXX reinvent dict(cgi.parse_qsl)
    queries = [ i for i in query[1].split('&')]
    query_dict = dict([i.split('=',1) for i in queries if '=' in i])
    query_dict.update(dict([(i,'') for i in queries if '=' not in i]))
    return query_dict

# XXX reinvent urlunquote
def urlunquote(string):
    url = string.split('%')
    return url[0] + ''.join([ chr(int(i[:2], 16)) + i[2:] 
                              for i in url[1:] ])

#XXX revinent urllib.splitquery
query = query_dict(came_from)
if query:
    referer = query.get('referer', referer)
    if referer:
        referer = urlunquote(referer)

plone_utils = getToolByName(portal, 'plone_utils')
plone_utils.addPortalMessage(utranslate('opencore',_(u'psm_not_sufficient_perms', u"You do not have sufficient permissions.")))

if referer.split('?')[0].endswith('/require_login'):
    referer = dummy_referer
state.setNextAction('redirect_to:string:%s' % referer)
return state
