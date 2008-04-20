## Script (Python) "showEditableBorder"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=template_id=None, allowed_types=None, actions=None
##title=returns whether or not current template displays *editable* border
##

# turn border on nearly all the time

from Products.CMFCore.utils import getToolByName
request = context.REQUEST

if actions is None:
    raise AttributeError, 'You must pass in the filtered actions'
    
if request.has_key('disable_border'): #short circuit
    return 0
else:
    outside = False

    proj_info = context.restrictedTraverse('@@project_info')
    mem_info = context.restrictedTraverse('@@member_info')
    if not proj_info.inProject and not mem_info.inMemberArea:
        outside = True

    if outside:
        mtool = getToolByName(context, 'portal_membership')
        if not mtool.checkPermission('Modify portal content', context):
            return 0
    
return 1
