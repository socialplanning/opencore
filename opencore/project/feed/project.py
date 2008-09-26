from AccessControl import getSecurityManager
from Acquisition import aq_inner
from DateTime import DateTime
from opencore.interfaces import IProject
from opencore.feed.base import BaseFeedAdapter
from opencore.feed.interfaces import IFeedData
from opencore.utils import interface_in_aq_chain
from opencore.utils import get_rel_url_for
from zope.component import adapts
from zope.interface import implements

def wiki_feed_listener(page, event):
    """ event subscriber that adds items to a project wiki feed """
    proj = interface_in_aq_chain(aq_inner(page), IProject)
    if proj is None:
        return
    feed = IFeedData(proj)
    title = page.Title()
    description = page.Description()
    rel_link = get_rel_url_for(page)
    pubDate = DateTime()
    author = getSecurityManager().getUser().getId()
    feed.add_item(title=title,
                  description=description,
                  rel_link=rel_link,
                  author=author,
                  pubDate=pubDate,
                  byline='edited by')

class WikiFeedAdapter(BaseFeedAdapter):
    """feed for wiki page modifications in project"""
    
    implements(IFeedData)
    adapts(IProject)

    title = 'Pages'
 
    @property
    def link(self):
        # XXX this will become '%s/home'
        # how to get this?
        return '%s/project-home' % self.context.absolute_url()
