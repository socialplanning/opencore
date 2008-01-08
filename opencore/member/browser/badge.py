from opencore.browser.base import BaseView

class BadgeView(BaseView):
    """ inherit from baseview to get a little bit of crap """
    def get_member(self):
        mem_id = self.context.getId()
        member = self.portal.portal_memberdata[mem_id]
        return member
