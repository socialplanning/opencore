from Products.CMFCore.utils import getToolByName
from opencore.interfaces.adding import IAddProject
from opencore.interfaces import IProject
from opencore.feed.base import BaseFeedAdapter
from opencore.feed.interfaces import IFeedData
from opencore.feed.interfaces import IFeedItem
from zope.component import adapts
from zope.interface import alsoProvides
from zope.interface import implements

class ProjectFeedAdapter(BaseFeedAdapter):
    """feed for wiki page modifications in project
       XXX or should this be only for new pages?
       probably want this to be across all changes within the project
       including all featurelets
       maybe then we iterate through the feed across all featurelets,
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
            # the feed supports passing the "body" attribute
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
