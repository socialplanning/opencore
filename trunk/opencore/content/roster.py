from Products.CMFCore.permissions import View
from Products.Archetypes.public import registerType
from Products.TeamSpace.roster import TeamRoster

from Products.OpenPlans.config import PROJECTNAME
class OpenRoster(TeamRoster):
    """
    OpenCore roster object.
    """
    portal_type = meta_type = 'OpenRoster'
    archetype_name = 'Project Roster'

    content_icon = 'openproject_icon.png'

    _at_rename_after_creation = True

    actions=(
        {'name':        'Project Roster',
         'id':          'view',
         'action':      'string:${object_url}',
         'permissions': (View,),
         'category'   : 'object',
         },
        )

    aliases = {
        '(Default)'    : 'roster_view',
        'edit'         : 'base_edit',
        'gethtml'      : '',
        'index.html'   : '',
        'properties'   : '',
        'sharing'      : '',
        'subscribers'  : '',
        'view'         : '(Default)',
        }

registerType(OpenRoster, package=PROJECTNAME)

