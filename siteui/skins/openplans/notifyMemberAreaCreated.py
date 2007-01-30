## Script (Python) "notifyMemberAreaCreated"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=
##title=Create the member home page

from Products.CMFCore.utils import getToolByName
mtool = getToolByName(context, 'portal_membership')
#member_id = mtool.getAuthenticatedMember().getId()
#folder = mtool.getHomeFolder(member_id)
#page_id = "%s-home" % member_id
#title = "%s Home" % member_id
#folder.invokeFactory('Document', page_id, title=title)
#folder.setDefaultPage(page_id)
#
#page = getattr(folder, page_id)
#page_text = context.member_index(member_id=member_id)
#page.setText(page_text)


member = mtool.getAuthenticatedMember()

from opencore.siteui.memberprofile import notifyFirstLogin
notifyFirstLogint(member)
