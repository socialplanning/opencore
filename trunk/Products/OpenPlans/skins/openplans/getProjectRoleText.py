## Script (Python) "getProjectRoleText"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=proj
##title=Get text for the project role for current member
##
ordered_roles = ('ProjectAdmin', 'ProjectMember')
roles_text_map = {'ProjectAdmin': 'an Administrator for',
                  'ProjectMember': 'a Member of'}
mem_roles = proj.getTeamRolesForAuthMember()
if not mem_roles:
    return 'not a Member of'
elif len(mem_roles) == 1:
    return roles_text_map[mem_roles[0]]
else:
    for role in ordered_roles:
        if role in mem_roles:
            return roles_text_map[role]

