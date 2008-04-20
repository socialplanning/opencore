import transaction

from Products.CMFCore.utils import getToolByName
from Products.ATContentTypes.migration.migrator import CMFItemMigrator
from Products.ATContentTypes.migration.walker import CatalogWalker

team_map = {}

class MemberMigrator(CMFItemMigrator):
    """
    Migrates from Member to OpenMember
    """
    src_portal_type = src_meta_type = 'Member'
    dst_portal_type = dst_meta_type = 'OpenMember'
    map = {'fullname': 'fullname',
           'email': 'email',
           'getPortrait': 'setPortrait',
           'location': 'location',
           'Description': 'setDescription',
           }

    def beforeChange_storeTeams(self):
        tmtool = getToolByName(self.old, 'portal_teams')
        teams = tmtool.getTeamsByMemberId(self.old.getId())
        team_map[self.old.getId()] = [t.getId() for t in teams]
        for team in teams:
            team.removeMember(self.old.getId())

def migrate_members(self):
    portal = getToolByName(self, 'portal_url').getPortalObject()
    walker = CatalogWalker(portal, MemberMigrator)
    transaction.commit(1)
    
    walker.go()

    tmtool= getToolByName(self, 'portal_teams')
    for m_id, tm_ids in team_map.items():
        for tm_id in tm_ids:
            tm = tmtool.getTeamById(tm_id)
            tm.addMember(m_id)

    return "Done."
