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

    def rosterSearchResults(self, REQUEST=None, **kw):
        """
        Override the default since we can go to the catalog.
        """
        kw = kw.copy()
        kw[USER_ID_VARIABLE] = self.getActiveMemberIds()
        mbtool = getToolByName(self, 'membrane_tool')
        results = mcat_tool.searchResults(REQUEST=REQUEST, **kw)
        return results


registerType(OpenRoster, package=PROJECTNAME)

