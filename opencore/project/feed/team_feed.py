from opencore.feed.browser.view import FeedView
from opencore.feed.interfaces import IFeedData
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from zope.component import getAdapter

class BlankSlateTeamFeedView(FeedView):
    
    blankslate = 'team_blank_slate.pt'

    def __init__(self, context, request):
        adapted = getAdapter(context, IFeedData, 'team')
        super(FeedView, self).__init__(adapted, request)
        self.n_members = len(context.projectMemberIds())
        if self.n_members < 2 and context.isProjectAdmin():
            self.index = ZopeTwoPageTemplateFile(self.blankslate)

    def number_of_members(self):
        if self.n_members == 1:
            return '1 member'
        return '%s members' % self.n_members
