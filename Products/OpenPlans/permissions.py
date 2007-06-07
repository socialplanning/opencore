from Products.CMFCore.CMFCorePermissions import setDefaultRoles, \
     AddPortalMember
from Products.TeamSpace.permissions import ManageTeamMembership
from Products.kupu.plone.permissions import QueryLibraries
from Products.listen.permissions import AddMailingList, SubscribeSelf, \
     ManageSubscriptions, InviteSubscribers
import Products.Archetypes.public as atapi
import config

CopyOrMove = "Copy or Move"

MakeContentVisible = "OpenPlans: Make content visible"
ManageWorkflowPolicy = "OpenPlans: Manage workflow policy"

DEFAULT_PERMISSIONS_DATA = (
    (['Manager', 'Owner', 'ProjectContentMgr', 'ProjectAdmin',
      'ProjectMember', 'Reviewer'],
     ['Add portal content', 'Add portal folders',
      'Add Documents, Images, and Files',
      'ATContentTypes: Add Document', 'ATContentTypes: Add Event',
      'ATContentTypes: Add File', 'ATContentTypes: Add Folder',
      'ATContentTypes: Add Image', 'ATContentTypes: Add Link',
      'ATContentTypes: Add News Item', 'OpenPlans: Add OpenPage',
      'Reply to item', 'Delete objects', CopyOrMove]),

    (['Manager', 'Owner', 'ProjectContentMgr', 'ProjectAdmin',
      'ProjectMember', 'Reviewer', 'Member'],
     [QueryLibraries]),

    (['Manager', 'Owner', 'ProjectContentMgr', 'ProjectAdmin',
      'ProjectMember', 'Reviewer', 'Member', 'Anonymous'],
     [SubscribeSelf]),

    (['Manager', 'Owner', 'ProjectContentMgr', 'ProjectAdmin',
      'Reviewer'],
     ['List folder contents',
      'Quills: Add WeblogEntry', 'Quills: Add WeblogTopic',
      'Quills: Add WeblogArchive',]),

    (['Manager', 'ProjectAdmin', 'Owner'],
     [ManageTeamMembership, 'TeamSpace: Manage team',
      ManageWorkflowPolicy, AddMailingList, InviteSubscribers]),

    (['Manager', 'ProjectAdmin', 'ProjectContentMgr',],
     [MakeContentVisible,]),

    (['Manager',],
     [ManageSubscriptions,]),

    (['Anonymous'],
     ['Add portal member',]),
    )

DEFAULT_PFOLDER_PERMISSIONS_DATA = (
    (['Manager', 'Member'],
     ['OpenPlans: Add OpenProject', 'OpenPlans: Add OpenPage',
       'ATContentTypes: Add Image', 'Add portal content',]
     ),
    )

PLACEFUL_PERMISSIONS_DATA = {
    'portal_teams': ((['Manager',],
                      ['List folder contents']),
                     )
    }

ADD_DEFAULT_ROLES = {
    'OpenRoster': ('Manager', 'ProjectAdmin', 'Owner'),
    }

def initialize():
    permissions = {}
    types = atapi.listTypes(config.PROJECTNAME)
    for atype in  types:
        typename = atype['name']
        if typename == 'OpenMember':
            permissions[atype['portal_type']] = AddPortalMember
        elif typename == 'OpenMembership':
            permissions[atype['portal_type']] = ManageTeamMembership
        else:
            permission = "%s: Add %s" % (config.PROJECTNAME, atype['portal_type'])
            permissions[atype['portal_type']] = permission
            # Assign default roles
            if ADD_DEFAULT_ROLES.has_key(typename):
                setDefaultRoles(permission, ADD_DEFAULT_ROLES[typename])
            else:
                setDefaultRoles(permission, ('Manager',))
    permission = MakeContentVisible
    setDefaultRoles(permission, ('Manager',))

    return permissions
