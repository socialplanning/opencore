from Products.CMFCore.utils import getToolByName
from opencore.interfaces.adding import IAddProject
from opencore.interfaces import IProject
from opencore.feed.base import BaseFeedAdapter
from opencore.feed.interfaces import IFeedData
from opencore.feed.interfaces import IFeedItem
from zope.component import adapts
from zope.interface import alsoProvides
from zope.interface import implements

class ProjectsFeedAdapter(BaseFeedAdapter):
    """feed for new projects"""
    
    implements(IFeedData)
    adapts(IAddProject)

    @property
    def items(self):
        cat = getToolByName(self.context, 'portal_catalog')
        #XXX put in max depth 1 to not search subfolders
        for brain in cat(portal_type='OpenProject',
                              sort_on='created',
                              sort_order='descending',
                              sort_limit=10):

            title = brain.Title
            description = brain.Description
            link = brain.getURL()
            pubDate = brain.created

            # returning a dictionary would also work
            # this is just more formal
            feed_item = type('ProjectFeedItem',
                             (object,),
                             dict(title=title,
                                  description=description,
                                  link=link,
                                  pubDate=pubDate,
                                  ))

            # to be technically correct
            alsoProvides(feed_item, IFeedItem)
            
            yield feed_item
