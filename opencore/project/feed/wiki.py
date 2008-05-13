from opencore.browser.blankslate import BlankSlateViewlet
from Products.CMFCore.utils import getToolByName
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
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
        cat = getToolByName(self.context, 'portal_catalog')
        brains = cat(portal_type='Document',
                     path='/'.join(self.context.getPhysicalPath()))

        # there may be no catalog results for wiki pages
        # if the user has recently become a member of this project
        # and it's a closed project; this is because the catalog is
        # reindexed asynchronously to reflect the user's new role
        # (that is, that he can see the closed project's contents)
        if len(brains) == 0:
            return True

        if len(brains) > 1:
            return False
        histories = brains[0].getObject().getHistories()
        return len(list(histories)) < 2
