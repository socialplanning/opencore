import opencore.feed.browser
import os

from zope.component import getAdapter
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from opencore.browser.blankslate import BlankSlateViewlet
from opencore.feed.interfaces import IFeedData

class DiscussionsSummaryViewlet(BlankSlateViewlet):

    blank_template = ZopeTwoPageTemplateFile('lists_blank_slate.pt')
    template = os.path.join(os.path.dirname(opencore.feed.browser.__file__), 'feed_snippet.pt')
    template = ZopeTwoPageTemplateFile(template)

    sort_order = 200

    def is_blank(self):
        if self.context.items:
            return False
        if self.context.mlists:
            self.create = os.path.join(self.context.context.absolute_url(), self.context.mlists[0], 'archive', 'new_topic')
        else:
            self.create = os.path.join(self.context.context.absolute_url(), 'create')
        return True

    def adapt(self):
        return getAdapter(self.context.lists, IFeedData)

