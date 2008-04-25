from Products.Five.viewlet.viewlet import ViewletBase
from opencore.feed.interfaces import IFeedData
from topp.utils.pretty_date import prettyDate
from zope.component import getAdapter

class BlankSlateViewlet(ViewletBase):
    """Base superclass for viewlets that want to abstract out
       whether to show a 'blank' version of a template or one with data"""

    adapter_name = ''

    def render(self):
        # sub-classes must specify a blank template and a template
        assert self.blank_template and self.template
        # and an is_blank function
        assert self.is_blank

        self.feed = self.adapt()

        if self.is_blank():
            return self.blank_template()
        else:
            return self.template()

    def adapt(self):
        return getAdapter(self.context, IFeedData, self.adapter_name)

    def pretty_date(self, date):
        # XXX this is copy/pasted
        return prettyDate(date)

