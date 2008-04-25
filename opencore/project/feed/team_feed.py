from opencore.feed.browser.view import FeedView
from opencore.feed.interfaces import IFeedData
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from zope.component import getAdapter

class BlankSlateTeamFeedView(FeedView):
    
    blankslate = 'team_blank_slate.pt'

    def __init__(self, context, request):
        super(FeedView, self).__init__(context, request)
        # really shouldn't be doing this much work in a constructor
        self.feed = getAdapter(context, IFeedData, 'team')
        self.n_members = len(context.projectMemberIds())
        if self.n_members < 2 and context.isProjectAdmin():
            self.index = ZopeTwoPageTemplateFile(self.blankslate)

    def number_of_members(self):
        if self.n_members == 1:
            return '1 member'
        return '%s members' % self.n_members
