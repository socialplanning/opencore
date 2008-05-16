from opencore.feed.base import BaseFeedAdapter
from opencore.feed.interfaces import IFeedData
from opencore.interfaces import IProject
from opencore.member.utils import profile_path
from Products.CMFCore.utils import getToolByName
from zope.component import adapts
from zope.interface import implements

def portrait_sort_key(member):
    """sorting function for member display by portrait"""
    return member.has_portrait

class TeamFeedAdapter(BaseFeedAdapter):
    implements(IFeedData)
    adapts(IProject)

    title = 'Team'

    @property
    def link(self):
        return '%s/team' % self.context.absolute_url()

    def items(self, n_items=12):
        if hasattr(self,'_items'):
            # If the property already contains something, there's no need to
            # regenerate it.
            return self._items

        project = self.context
#        members = list(project.projectMembers())
        members = project.projectMemberBrains()

        # XXX should probably go in Products.Openplans' project
        # maybe related to docstring above while filtering by hand is necessary?
        team = project.getTeams()[0]
        wf = getToolByName(project, 'portal_workflow')
        members = [ member for member in members 
                    if wf.getInfoFor(team.getMembershipByMemberId(member.getId), 'review_state') == 'public' ]

        members.sort(key=portrait_sort_key, reverse=True) # could also sort by admin-ness, lastlogin, etc
        members = members[:n_items]

        for member in members:
            link = profile_path(member.getId)
            self.add_item(title=member.getId,
                          description=member.getFullname,
                          link=link,
                          author=member.getId,
                          pubDate=member.getLast_login_time)

        return self._items
