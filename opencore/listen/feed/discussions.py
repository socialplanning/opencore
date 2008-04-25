import opencore.feed.browser
import os

from zope.component import getAdapter
from zope.component import getUtility
from Acquisition import aq_inner
from Acquisition import aq_parent
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from Products.listen.interfaces import ISearchableArchive
from opencore.browser.blankslate import BlankSlateViewlet
from opencore.feed.interfaces import IFeedData

class DiscussionsSummaryViewlet(BlankSlateViewlet):

    blank_template = ZopeTwoPageTemplateFile('lists_blank_slate.pt')
    template = os.path.join(os.path.dirname(opencore.feed.browser.__file__),
                            'feed_snippet.pt')
    template = ZopeTwoPageTemplateFile(template)

    sort_order = 200

    @property
    def listfolder(self):
        """
        returns the lists folder w/ a clean aq chain
        """
        clean_project = aq_inner(self.context)
        # XXX hardcoded folder id == bad
        return clean_project._getOb('lists', None)

    def is_blank(self):
        listfolder = self.listfolder
        if listfolder is None:
            return True
        for ml_id in self.feed.mlists:
            mlist = listfolder._getOb(ml_id)
            archive = getUtility(ISearchableArchive, context=mlist)
            if archive.getToplevelMessages():
                return False
        if self.feed.mlists:
            self.create = os.path.join(self.context.absolute_url(),
                                       self.feed.mlists[0],
                                       'archive','new_topic')
        else:
            self.create = os.path.join(self.context.absolute_url(), 'create')
        return True

    def adapt(self):
        return IFeedData(self.listfolder, None)
