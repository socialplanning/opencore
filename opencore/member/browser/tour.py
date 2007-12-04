from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from opencore.member.browser.account import MemberAccountView

class TourView(MemberAccountView):
    """ dummy view for the 1page tour """

    template = ZopeTwoPageTemplateFile('tour.pt')

    def has_projects(self):
        if self.invitations() or self.projects_for_user:
            return True
        return False
