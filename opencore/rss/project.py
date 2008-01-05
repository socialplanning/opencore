from Products.CMFCore.utils import getToolByName
from opencore.interfaces.adding import IAddProject
from opencore.interfaces import IProject
from opencore.rss.base import BaseFeedAdapter
from opencore.rss.interfaces import IFeedData
from opencore.rss.interfaces import IFeedItem
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

class ProjectFeedAdapter(BaseFeedAdapter):
    """rss for wiki page modifications in project
       XXX or should this be only for new pages?
       probably want this to be across all changes within the project
       including all featurelets
       maybe then we iterate through the rss across all featurelets,
       parse them, and aggregate with latest pages"""
    
    implements(IFeedData)
    adapts(IProject)

    @property
    def items(self):
        cat = getToolByName(self.context, 'portal_catalog')
        for brain in cat(portal_type='Document',
                         path='/'.join(self.context.getPhysicalPath()),
                         sort_on='modified',
                         sort_order='descending',
                         sort_limit=10):

            title = brain.Title
            #XXX would be nice if the description was the revision note
            #maybe we should index it that way?
            description = brain.Description
            link = brain.getURL()
            pubDate = brain.modified
            #XXX maybe we should stick the body in here as well?
            # the rss feed supports passing the "body" attribute
            # problem though, is that we don't want to put all of it in there
            # and if we cut it off, we might cut off some html
            # let's just leave it off for now
            #body = brain.getObject().getText()

            # returning a dictionary would also work
            # this is just more formal
            feed_item = type('PageFeedItem',
                             (object,),
                             dict(title=title,
                                  description=description,
                                  link=link,
                                  pubDate=pubDate,
                                  #body=body,
                                  ))

            # to be technically correct
            alsoProvides(feed_item, IFeedItem)
            
            yield feed_item
