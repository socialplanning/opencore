"""
separate pre-confirmed view for folks already invited to a project
"""
# @@ join should move in here too

from opencore.nui.account import accountview
from opencore.nui.formhandler import action, post_only
from opencore.nui.base import view
from opencore.nui.project.interfaces import IEmailInvites
from zope.component import getUtility
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile


class InviteJoinView(accountview.JoinView):
    """a preconfirmed join view that also introspects any invitation a
    perspective member has"""

    template = ZopeTwoPageTemplateFile('invite-join.pt')


    def do_project_joins(self, member, project_ids):
        for proj_id in self.project_ids:
            continue
    
    @view.memoizedproperty
    def invite_util(self):
        return getUtility(IEmailInvites)
    
    @view.memoizedproperty
    def email(self):
        return self.request.get('email')

    @view.memoizedproperty
    def invites(self):
        return self.invite_util.getInvitesByEmailAddress(self.email)

    @view.memoizedproperty
    def sorted_invites(self):
        return sorted(self.invites)

    @view.memoizedproperty
    def invite_map(self):
        return [dict(id=invite, title=self.proj_title(invite)) \
                for invite in self.invites]

    @action('join', apply=post_only(raise_=False))
    def create_member(self, targets=None, fields=None):
        key = self.request.get('__k')
        import zExceptions
        if not key:
            raise zExceptions.BadRequest("Must present proper validation")
        if int(key) != self.invites.key:
            raise ValueError('Bad confirmation key')
        member = super(InviteJoinView, self)._create_member(targets, fields, confirmed=True)
        self.do_project_joins(member, self.request.get('invited_projects'))        

    def proj_title(self, invite):
        proj_obj = self.context.projects.get(invite)
        if proj_obj is not None:
            return proj_obj.Title()
        return None
