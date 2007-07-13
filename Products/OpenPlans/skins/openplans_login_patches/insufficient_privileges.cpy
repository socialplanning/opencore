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
portal_membership = getToolByName(portal, 'portal_membership')
member = portal_membership.getAuthenticatedMember()
member_folder = portal_membership.getHomeFolder(member.getId())
dummy_referer = '%s/preferences' % member_folder.absolute_url()
referer = context.REQUEST.environ.get('HTTP_REFERER', 
                                      dummy_referer)
came_from = context.REQUEST.form.get('came_from', '')

#XXX This should all be refactored!
#XXX maybe put this in a view somewhere

# XXX you can't import things in skins :(
def query_dict(string):

    # XXX reinvent urllib.splitquery
    query = string.split('?')
    if len(query) != 2:
        return None

    # XXX reinvent dict(cgi.parse_qsl)
    return dict([i.split('=') for i in query[1].split('&')])

# XXX reinvent urlunquote
def urlunquote(string):
    url = string.split('%')
    return url[0] + ''.join([ chr(int(i[:2], 16)) + i[2:] 
                              for i in url[1:] ])

#XXX revinent urllib.splitquery
query = query_dict(came_from)
if query:
    referer = query.get('referer')
    if referer:
        referer = urlunquote(referer)

plone_utils = getToolByName(portal, 'plone_utils')
plone_utils.addPortalMessage(_('Insufficient Privileges'))

if referer.split('?')[0].endswith('/require_login'):
    referer = dummy_referer
state.setNextAction('redirect_to:string:%s' % referer)
return state
