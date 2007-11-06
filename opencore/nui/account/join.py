"""
separate pre-confirmed view for folks already invited to a project
"""
from opencore.nui.account import accountview
from opencore.nui.formhandler import action, post_only, OctopoLite
from opencore.nui.formhandler import anon_only
from opencore.nui.base import view
from opencore.nui.project.interfaces import IEmailInvites
from zope.component import getUtility
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from opencore.nui.base import BaseView
from zope.event import notify
from zope.app.event.objectevent import ObjectCreatedEvent
from opencore.nui.base import BaseView, _


class JoinView(accountview.AccountView, OctopoLite):

    template = ZopeTwoPageTemplateFile('join.pt')

    @anon_only(BaseView.siteURL)
    def handle_request(self):
        """ redirect logged in users """

    def _create_member(self, targets=None, fields=None, confirmed=False):
        mdc = self.get_tool('portal_memberdata')
        mem = mdc._validation_member

        self.errors = {}
        
        self.errors = mem.validate(REQUEST=self.request,
                                   errors=self.errors,
                                   data=1, metadata=0)
        password = self.request.form.get('password')
        password2 = self.request.form.get('confirm_password')
        if not password and not password2:
            self.errors.update(dict(password=_(u'no_password', u'Please enter a password')))

        if self.errors:
            return self.errors

        # create a member in portal factory
        mdc = self.get_tool('portal_memberdata')
        pf = mdc.portal_factory

        #00 pythonscript call, move to fs code
        id_ = self.context.generateUniqueId('OpenMember')

        mem_folder = pf._getTempFolder('OpenMember')
        mem = mem_folder.restrictedTraverse('%s' % id_)

        # now we have mem, a temp member. create him for real.
        mem_id = self.request.form.get('id')
        mem = pf.doCreate(mem, mem_id)
        self.txn_note('Created %s with id %s in %s' % \
                      (mem.getTypeInfo().getId(),
                       mem_id,
                       self.context.absolute_url()))
        result = mem.processForm()
        notify(ObjectCreatedEvent(mem))
        mem.setUserConfirmationCode()
        mem_name = mem.getFullname()
        mem_name = mem_name or mem_id
        url = self._confirmation_url(mem)
        if accountview.email_confirmation():
            if not confirmed:
                self._sendmail_to_pendinguser(user_name=mem_name,
                                              email=self.request.get('email'),
                                              url=url)
            
                self.addPortalStatusMessage(_(u'psm_thankyou_for_joining',
                                              u'Thanks for joining ${portal_title}, ${mem_id}!\nA confirmation email has been sent to you with instructions on activating your account.',
                                              mapping={u'mem_id':mem_id,
                                                       u'portal_title':self.portal_title()}))
                self.redirect(self.portal_url())
            return mdc._getOb(mem_id)
        self.redirect(url)
        return mem

    create_member = action('join', apply=post_only(raise_=False))(_create_member)

    @action('validate')
    def validate(self, targets=None, fields=None):
        """ this is really dumb. """
        mdc = self.get_tool('portal_memberdata')
        mem = mdc._validation_member
        errors = {}
        errors = mem.validate(REQUEST=self.request,
                              errors=self.errors,
                              data=1, metadata=0)
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
        member = self.membranetool.unrestrictedSearchResults(getEmail=email)
        if member:
            member = member[0].getObject()
        
        return self.redirect(self._confirmation_url(member))
