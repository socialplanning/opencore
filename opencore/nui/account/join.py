"""
Join Views

* normal join view
* separate pre-confirmed view for folks already invited to a project
"""
from opencore.member.interfaces import ICreateMembers
from opencore.interfaces.event import JoinedProjectEvent
from opencore.nui.account import accountview
from opencore.browser.formhandler import action, post_only, OctopoLite
from opencore.browser.formhandler import anon_only
from opencore.browser.base import view
from opencore.interfaces.membership import IEmailInvites
from zope.component import getUtility
from zope.event import notify
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from opencore.browser.base import BaseView
from zope.event import notify
from zope.app.event.objectevent import ObjectCreatedEvent
from opencore.browser.base import BaseView, _


class JoinView(accountview.AccountView, OctopoLite):

    template = ZopeTwoPageTemplateFile('join.pt')

    @anon_only(BaseView.siteURL)
    def handle_request(self):
        """ redirect logged in users """

    def _create_member(self, targets=None, fields=None, confirmed=False):
        factory = ICreateMembers(self.portal)

        self.errors = factory.validate(self.request.form)
        if self.errors:
            return self.errors

        mem = factory.create(self.request.form)
        mem_name = mem.getFullname() or mem.getId()
        url = self._confirmation_url(mem)
        if accountview.email_confirmation():
            if not confirmed:
                self._sendmail_to_pendinguser(user_name=mem_name,
                                              email=self.request.get('email'),
                                              url=url)
            
                self.addPortalStatusMessage(_(u'psm_thankyou_for_joining',
                                              u'Thanks for joining ${portal_title}, ${mem_id}!\nA confirmation email has been sent to you with instructions on activating your account.',
                                              mapping={u'mem_id':mem.getId(),
                                                       u'portal_title':self.portal_title()}))
                self.redirect(self.portal_url())
            return mem
        self.redirect(url)
        return mem

    create_member = action('join', apply=post_only(raise_=False))(_create_member)

    @action('validate')
    def validate(self, targets=None, fields=None):
        """ this is really dumb. """
        errors = ICreateMembers(self.portal).validate(self.request.form)

        erase = [error for error in errors if error not in self.request.form]
        also_erase = [field for field in self.request.form if field not in errors]
        for e in erase + also_erase:
            errors[e] = ''
        ret = {}
        for e in errors:
            ret['oc-%s-error' % e] = {
                'html': str(errors[e]),
                'action': 'copy', 'effects': 'highlight'}
        return ret


class InviteJoinView(JoinView, accountview.ConfirmAccountView):
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

    def validate_key(self):
        key = self.request.form.get('__k')
        import zExceptions
        if not key:
            raise zExceptions.BadRequest("Must present proper validation")
        if key != self.invites.key:
            raise ValueError('Bad confirmation key')
        return True

    @action('join', apply=post_only(raise_=False))
    def create_member(self, targets=None, fields=None):
        self.validate_key()
        # do all the member making stuff
        member = super(InviteJoinView, self)._create_member(targets, fields, confirmed=True)
        if isinstance(member, dict):
            # return errors 
            return member

        self.confirm(member)
        self.login(member.getId())
        self.do_invite_joins(member)
        return self.redirect("%s/init-login" %self.siteURL)

    def do_invite_joins(self, member):
        """do the joins and activations"""
        mships = self.invite_util.convertInvitesForMember(member)
        for mship in mships:
            mship._v_self_approved = True
            if mship.aq_parent.getId() in self.proj_ids:
                mship.do_transition('approve_public')
            notify(JoinedProjectEvent(mship))
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
        if self.is_pending(getEmail=email):
            return self.redirect(self._confirmation_url(member))

        return None
