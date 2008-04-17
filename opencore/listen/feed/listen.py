import re

from Products.CMFCore.utils import getToolByName
from opencore.listen.interfaces import IOpenMailingList
from Products.listen.interfaces import ISearchableArchive
from Products.listen.lib.browser_utils import messageStructure
from opencore.featurelets.interfaces import IListenContainer
from opencore.feed.base import BaseFeedAdapter
from opencore.feed.base import FeedItemResponses
from opencore.feed.interfaces import IFeedData
from opencore.feed.interfaces import IFeedItem
from zope.component import adapts
from zope.component import getUtility
from zope.component import createObject
from zope.interface import alsoProvides
from zope.interface import implements

# regular expression to strip names from an email
# address in standard format
email_re = re.compile(r' *"(.*)" *<.*@.*>')

class ListsFeedAdapter(BaseFeedAdapter):
    implements(IFeedData)
    adapts(IListenContainer)

    title = 'Discussions'

    def is_project_member(self):
        project = self.context.aq_parent
        membertool = getToolByName(project, 'portal_membership')
        mem_id = membertool.getAuthenticatedMember().getId()
        team_ids = project.getTeams()[0].getActiveMemberIds()
        return mem_id in team_ids

    @property
    def mlists(self):
        return self.context.objectIds()

    def threads(self, mlist):
        archive = getUtility(ISearchableArchive, context=mlist)
        threads = archive.getToplevelMessages()        

    @property
    def items(self, n_items=5):
        """we aggregate the most recent messages across all mailing lists,
           then sort those by date and take the top n_items

           XXX this is potentially an expensive operation
           we may want a separate catalog on the lists level
           or store the mail messages in the main portal catalog as well
           in which case we would be able to search for messages
           in the site wide search"""

        if hasattr(self,'_items'):
            # If the property already contains something, there's no need to
            # regenerate it.
            return self._items

        MSG_BODY_LENGTH = 300

        items = []
        messages = []
        mlists = self.mlists
        n_lists = len(mlists)
        for ml_id in mlists:
            mlist = self.context._getOb(ml_id)
            archive = getUtility(ISearchableArchive, context=mlist)
            threads = archive.getToplevelMessages()

            def latest_reply(message):
                """given a message, get the latest reply in the thread"""
                # XXX this should really go in listen
                prev = next = message
                while next:
                    if next.date > prev.date:
                        prev = next
                    next = archive.getNextInThread(next.message_id)
                return prev

            threads = [ dict(message=message, 
                             reply=latest_reply(message), 
                             mlist=mlist)
                        for message in threads ]
            messages.extend(threads)
            
        date = lambda x: x['reply'].modification_date
        messages.sort(key=date, reverse=True)
        messages = messages[:n_items]

        for message in messages:
            #XXX
            # we get the object for now to see the body of the message
            # we can either add it to the metadata, or forget about it
            # or maybe something more clever?
            #             msg = brain.getObject()
            
            reply = message['reply']
            mlist = message['mlist']
            message = message['message']

            structure = messageStructure(message,
                                         sub_mgr=mlist)
            reply_structure = messageStructure(reply,
                                               sub_mgr=mlist)
            
            link = '%s/forum_view' % structure['url'].rstrip('/')
            reply_url = '%s#%s' % ( link, reply_structure['id'] )

            pubDate = reply.modification_date
            
            author = reply_structure['from_id']
            if not author:
                author = reply_structure['mail_from']
                match = re.match(email_re, author)
                if match:
                    author = match.groups()[0]

            title = structure['subject']
            description = structure['subject']

            # if more than one mailing list, it should be noted
            context = None
            if n_lists > 1:
                context = { 'title': mlist.title,
                            'link': mlist.absolute_url }

            # deal with responses
            responses = message.responses
            if responses:
                byline = 'latest by'
                response = FeedItemResponses(responses, reply_url)
            else:
                response = None
                byline = 'by'

            self.add_item(title=title,
                          description=description,
                          link=link,
                          author=author,
                          pubDate=pubDate,
                          context=context,
                          byline=byline,
                          responses=response)
        return self._items


#XXX duplication between this class and lists class above
# can factor out common behavior to a separate function/superclass
# OR (better) can make the MailingListsFeed consume the MailingListFeed
class MailingListFeedAdapter(BaseFeedAdapter):
    implements(IFeedData)
    adapts(IOpenMailingList)

    @property
    def items(self, n_items=5):
        """feed for first messages in a mailing list

           XXX somewhat expensive in that we get n_items mailing list objects
           but I think that these are somewhat lightweight in that they
           inherit from OFS.Folder
           """

        MSG_BODY_LENGTH = 300

        items = []
        brains = []
        sa = getUtility(
            ISearchableArchive,
            context=self.context)
        brains = sa.searchResults(sort_on='modification_date',
                                  sort_order='descending',
                                  sort_limit=n_items)

        for brain in brains:
            #XXX
            # we get the object for now to see the body of the message
            # we can either add it to the metadata, or forget about it
            # or maybe something more clever?
            msg = brain.getObject()
            
            title = brain.subject
            # only put the first part of the body of long messages
            body = msg.body
            if len(body) > MSG_BODY_LENGTH:
                body = '%s ...' % body[:MSG_BODY_LENGTH-4]
            description = body
            link = brain.getURL()
            pubDate = brain.modification_date
            author = msg.owner_info()['id']

            feed_item = createObject('opencore.feed.feeditem',
                                     title,
                                     description,
                                     link,
                                     author,
                                     pubDate)
            items.append(feed_item)
        return items
