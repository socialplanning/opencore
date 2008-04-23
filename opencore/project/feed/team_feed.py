from opencore.feed.interfaces import IFeedData
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from topp.utils.pretty_date import prettyDate
import Acquisition
from zope.component import getAdapter
from zope.contentprovider.interfaces import IContentProvider
from zope.interface import implements

class BlankSlateTeamFeed(Acquisition.Implicit):
    # XXX this could be abstracted

    implements(IContentProvider)
    
    blank_template = ZopeTwoPageTemplateFile('team_blank_slate.pt')
    template = ZopeTwoPageTemplateFile('team_feed_snippet.pt')

    def __init__(self, context, request, view):
        adapted = getAdapter(context, IFeedData, 'team')
        self.context = adapted
        self.request = request
        self.view = view
        self.n_members = len(context.projectMemberIds())
        self.is_blank = self.n_members < 2 and context.isProjectAdmin()

    def number_of_members(self):
        if self.n_members == 1:
            return '1 member'
        return '%s members' % self.n_members

    def render(self):
        if self.is_blank:
            return self.blank_template()
        else:
            return self.template()

    def pretty_date(self, date):
        # XXX this is copy/pasted
        return prettyDate(date)

    def update(self):
        pass
