from opencore.browser.blankslate import BlankSlateViewlet
from opencore.member.utils import profile_path
from Products.CMFCore.utils import getToolByName
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from Products.Five.viewlet.viewlet import ViewletBase
import opencore.feed.browser
import os

class WikiSummaryViewlet(BlankSlateViewlet):
    blank_template = ZopeTwoPageTemplateFile('wiki_blank_slate.pt')
    template = os.path.join(os.path.dirname(opencore.feed.browser.__file__), 'feed_snippet.pt')
    template = ZopeTwoPageTemplateFile(template)

    sort_order = 300

    def is_blank(self):
        """If there's only one wiki page, and it has no history, than
        this is a blank slate"""
        cat = getToolByName(self.context.context, 'portal_catalog')
        brains = cat(portal_type='Document',
                     path='/'.join(self.context.context.getPhysicalPath()))
        if len(brains) > 1:
            return False
        histories = brains[0].getObject().getHistories()
        return len(list(histories)) < 2
