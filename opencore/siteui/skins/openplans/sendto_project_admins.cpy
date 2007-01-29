## Controller Python Script "sendto_project_admins"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind state=state
##bind subpath=traverse_subpath
##parameters=
##title=Send an URL to a friend
##
request=context.REQUEST

from Products.CMFCore.utils import getToolByName

anontool = getToolByName(context, 'portal_anonymailer')
project = context.ts_get_containing_space()
admins = project.users_with_local_role('ProjectAdmin')
msg_vars = {'recip_id': admins}
state_values = anontool.sendMessage(request.form, msg_vars,
                                    'project_admin_template')
return state.set(**state_values)
