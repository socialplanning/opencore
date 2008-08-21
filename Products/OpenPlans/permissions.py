from Products.CMFCore.permissions import setDefaultRoles
from Products.CMFCore.permissions import AddPortalMember
from Products.TeamSpace.permissions import ManageTeamMembership
from Products.SimpleAttachment.config import DEFAULT_ADD_CONTENT_PERMISSION as \
     AddAttachment

import Products.Archetypes.public as atapi
import config

CopyOrMove = "Copy or Move"

MakeContentVisible = "OpenPlans: Make content visible"
ManageWorkflowPolicy = "OpenPlans: Manage workflow policy"
ViewEmails = 'OpenPlans: View emails'

AddOpenPage = 'OpenPlans: Add OpenPage ' # XXX add defaults for this below.

DEFAULT_PFOLDER_PERMISSIONS_DATA = (
    (['Manager', 'Member'],
     ['OpenPlans: Add OpenProject', 'OpenPlans: Add OpenPage',
       'ATContentTypes: Add Image', 'Add portal content',]
     ),
    
    (['Manager', 'Owner', 'ProjectAdmin', 'ProjectMember'],
     ['OpenPlans: Add SubProject', ]
     ),
    )

PLACEFUL_PERMISSIONS_DATA = {
    'portal_teams': ((['Manager',],
                      ['List folder contents']),
                     )
    }

DEFAULT_ADD_PERMISSIONS = {
    'OpenMember': AddPortalMember,
    'OpenMembership': ManageTeamMembership,
    'ATBlobAttachment': AddAttachment,
    }

def initialize():
    permissions = {}
    types = atapi.listTypes(config.PROJECTNAME)

    for atype in types:
        typename = atype['name']
        if typename in DEFAULT_ADD_PERMISSIONS:
            permissions[atype['portal_type']] = DEFAULT_ADD_PERMISSIONS[typename]
        else:
            permission = "%s: Add %s" % (config.PROJECTNAME, atype['portal_type'])
            setDefaultRoles(permission, ('Manager',))
            permissions[atype['portal_type']] = permission

    perms_to_set = [MakeContentVisible, ViewEmails]
    for permission in perms_to_set:
        setDefaultRoles(permission, ('Manager',))

    return permissions
