from opencore.feed.base import BaseFeedAdapter
from opencore.feed.interfaces import IFeedData
from opencore.i18n import translate
from opencore.interfaces import IProject
from opencore.interfaces.event import ILeftProjectEvent
from opencore.member.utils import profile_path
from zope.component import adapts
from zope.component import getAdapter
from zope.interface import implements

def portrait_sort_key(member):
    """sorting function for member display by portrait"""
    return member.has_portrait

def team_feed_listener(mship, event):
    proj = mship.getTeam().getProject()
    feed = getAdapter(proj, IFeedData, name='team')
    member = mship.getMember()
    mem_id = member.getId()
    if ILeftProjectEvent.providedBy(event):
        verb = translate(u'removed', default='Removed')
    else:
        verb = translate(u'joined', default='Joined')
    title = u'%s - %s' % (mem_id, verb)
    description = u'%s - %s' % (member.getFullname(), verb)
    rel_link = profile_path(mem_id)
    feed.add_item(title=title,
                  description=description,
                  rel_link=rel_link,
                  author=mem_id,
                  pubDate=member.getLast_login_time())

class TeamFeedAdapter(BaseFeedAdapter):
    implements(IFeedData)
    adapts(IProject)

    title = 'Team'

    @property
    def link(self):
        return '%s/team' % self.context.absolute_url()
