"""
separate pre-confirmed view for folks already invited to a project
"""
# @@ join should move in here too

from opencore.nui.account import accountview
from opencore.nui.formhandler import action
from opencore.nui.base import memoizedproperty
from topp.clockqueue import AnnotationQueue
import time

class InviteJoinView(accountview.JoinView):
    """a preconfirmed join view that also introspects any invitation a
    perspective member has"""

    def _get_confirmation_email(self):
        pass

    def _get_invites(self):
        pass

    def do_project_joins(self, member, project_ids):
        pass
    
    @memoizedproperty
    def email(self):
        return self._get_confirmation_email(self.request.get('__k'))

    @memoizedproperty
    def invites(self):
        return self._get_invites(self.email)
    
    @action('join', apply=post_only(raise_=False))
    def create_member(self, targets=None, fields=None):
        email = self.confirm_confirmation(self.request.get('__k'))
        if not email:
            raise ValueError('Bad confirmation key')
        member = super(InviteJoinView, self).create_member(targets, fields, confirmed=True)
        self.do_project_joins(member, self.request.get('invited_projects'))        


class InviteKeys(AnnotationQueue):
    key = "opencore.account.invitejoin"

    def new_key(self, email, project_id):
        return hash((email, project_id, InviteKeys))
        

    def append_invite(self, email, project_id):
        pass
