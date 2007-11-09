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
request = context.REQUEST

from opencore.nui.member.miv import initializeMemberArea
initializeMemberArea(mtool, request, member_id=context.getId())
