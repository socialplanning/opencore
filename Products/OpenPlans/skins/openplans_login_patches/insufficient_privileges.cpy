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
                                      context.portal_url())
came_from = context.REQUEST.get('came_from', '')

#XXX This should all be refactored!
#XXX maybe put this in a view somewhere
#XXX alternatively, use cookies

#XXX revinent urllib.splitquery
query = came_from.split('?')
if len(query) == 2:

    #reinvent dict(cgi.parse_qsl)
    query = dict([i.split('=') for i in query[1].split('&')])

    if query.get('referer'):
        referer = query['referer']

        # XXX reinvent urlunquote
        referer = referer.split('%')
        referer = referer[0] + ''.join([ chr(int(i[:2], 16)) + i[2:] 
                                         for i in referer[1:] ])

plone_utils = getToolByName(portal, 'plone_utils')
plone_utils.addPortalMessage(_('Insufficient Privileges'))

state.setNextAction('redirect_to:string:%s' % referer)
return state
