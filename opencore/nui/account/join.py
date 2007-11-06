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


class InviteJoinView(accountview.JoinView, accountview.ConfirmAccountView):
    """a preconfirmed join view that also introspects any invitation a
    perspective member has"""

    template = ZopeTwoPageTemplateFile('invite-join.pt')

    @property
    def proj_ids(self):
        return self.request.get('invites', [])
        
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
        if self.invites:
            return [dict(id=invite, title=self.proj_title(invite)) \
                    for invite in self.invites]
        return tuple()

    @action('join', apply=post_only(raise_=False))
    def create_member(self, targets=None, fields=None):
        key = self.request.get('__k')
        import zExceptions
        if not key:
            raise zExceptions.BadRequest("Must present proper validation")
        if int(key) != self.invites.key:
            raise ValueError('Bad confirmation key')

        # do all the member making stuff
        member = super(InviteJoinView, self)._create_member(targets, fields, confirmed=True)
        if isinstance(member, dict): # @ some wierd octo shizzle?
            return member
        self.confirm(member)
        self.login(member.getId())

        # do the joins and activations
        mships = self.invite_util.convertInvitesForMember(member)
        for mship in mships:
            mship._v_self_approved = True
            if mship.aq_parent.getId() in self.proj_ids:
                mship.do_transition('approve_public')
        return self.redirect("%s/init-login" %self.siteURL)

    def proj_title(self, invite):
        proj_obj = self.context.projects.get(invite)
        if proj_obj is not None:
            return proj_obj.Title()
        return None

    def if_pending_user(self):
        """
        A valid key here is good enough for an email confirmation, so if the
        user already has a pending member object, we can just confirm that
        member by redirecting to the confirm-account view.
        """
        key = self.request.get('__k')
        import zExceptions
        if not key:
            raise zExceptions.BadRequest("Must present proper validation")
        if int(key) != self.invites.key:
            raise ValueError('Bad confirmation key')
        
        email = self.request.form.get("email")
        member = self.membranetool.unrrestrictedSearchResults(getEmail=email)
        if member:
            member = member[0].getObject()
        
        return self.redirect(self._confirmation_url(member))
