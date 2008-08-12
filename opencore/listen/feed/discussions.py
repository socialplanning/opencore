import opencore.feed.browser
import os
from Acquisition import aq_inner
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from opencore.browser.blankslate import BlankSlateViewlet
from opencore.feed.interfaces import IFeedData

class DiscussionsSummaryViewlet(BlankSlateViewlet):

    blank_template = ZopeTwoPageTemplateFile('lists_blank_slate.pt')
    template = os.path.join(os.path.dirname(opencore.feed.browser.__file__),
                            'feed_snippet.pt')
    template = ZopeTwoPageTemplateFile(template)

    sort_order = 200

    def listfolder(self):
        """ returns the 'lists' folder w/ a clean aq chain """
        clean_project = aq_inner(self.context)
        # XXX hardcoded folder id == bad
        return clean_project._getOb('lists', None)

    def is_blank(self):
        # XXX Confusing: where does self.feed come from?
        # It gets bound in the base class' render() method.
        if self.feed.items:
            return False
        if self.feed.mlists:
            self.create = '/'.join((self.listfolder().absolute_url(),
                                    self.feed.mlists[0],
                                    'archive', 'new_topic'))
        else:
            self.create = '/'.join((self.listfolder().absolute_url(), 'create'))
        return True

    def adapt(self):
        return IFeedData(self.listfolder(), None)
