from AccessControl import getSecurityManager
from Acquisition import aq_inner
from opencore.interfaces import IProject
from opencore.feed.base import BaseFeedAdapter
from opencore.feed.interfaces import IFeedData
from opencore.utils import find_interface_parent
from zope.component import adapts
from zope.interface import implements

def wiki_feed_listener(page, event):
    """ event subscriber that adds items to a project wiki feed """
    proj = find_interface_parent(aq_inner(page), IProject)
    if proj is None:
        return
    feed = IFeedData(proj)
    title = page.Title()
    description = page.Description()
    link = page.absolute_url() # dynamicize on retrieval
    pubDate = page.modified()
    author = getSecurityManager().getUser().getId()
    feed.add_item(title=title,
                  description=description,
                  link=link,
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
