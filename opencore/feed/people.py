from Products.CMFCore.utils import getToolByName
from opencore.interfaces.adding import IAmAPeopleFolder
from opencore.feed.base import BaseFeedAdapter
from opencore.feed.interfaces import IFeedData
from opencore.feed.interfaces import IFeedItem
from zope.component import adapts
from zope.interface import alsoProvides
from zope.interface import implements

class PeopleFeedAdapter(BaseFeedAdapter):
    implements(IFeedData)
    adapts(IAmAPeopleFolder)

    @property
    def items(self):
        cat = getToolByName(self.context, 'portal_catalog')
        #XXX put in max depth 1 to not search subfolders
        for brain in cat(portal_type='OpenMember',
                              sort_on='created',
                              sort_order='descending',
                              sort_limit=10):

            title = brain.Title
            # XXX we may want to stick the location in here
            # so something useful will show up in the feed
            description = brain.Description

            # XXX yes I know, this should be "nicer"
            # getting it the proper way is slower though
            # because we have to wake up more objects
            # mstool.getHomeFolder(brain.id)
            url = brain.getURL().replace('portal_memberdata', 'people')
            link = '%s/profile' % url

            pubDate = brain.created

            # returning a dictionary would also work
            # this is just more formal
            feed_item = type('MemberFeedItem',
                             (object,),
                             dict(title=title,
                                  description=description,
                                  link=link,
                                  pubDate=pubDate,
                                  ))

            # to be technically correct
            alsoProvides(feed_item, IFeedItem)
            
            yield feed_item
