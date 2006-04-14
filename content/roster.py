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
         'action':      'roster_view',
         'permissions': (View,),
         'category'   : 'object',
         },
        )

registerType(OpenRoster, package=PROJECTNAME)

