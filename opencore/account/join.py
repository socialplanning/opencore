"""
Join Views

* normal join view
* separate pre-confirmed view for folks already invited to a project
"""

from Products.CMFCore.utils import getToolByName
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from opencore.account import browser
from opencore.account import utils
from opencore.account.confirmation import ConfirmAccountView
from opencore.browser.base import BaseView
from opencore.browser.base import BaseView, _
from opencore.browser.base import view
from opencore.browser.formhandler import action, post_only, OctopoLite
from opencore.browser.formhandler import anon_only
from opencore.interfaces.event import JoinedProjectEvent
from opencore.interfaces.membership import IEmailInvites
from opencore.member.interfaces import ICreateMembers
from zope.app.event.objectevent import ObjectCreatedEvent
from zope.component import getUtility
from zope.event import notify
from topp.utils.pretty_text import truncate
import zExceptions

import urllib

class JoinView(browser.AccountView, OctopoLite):

    template = ZopeTwoPageTemplateFile('join.pt')

    def quote(self, txt):
        return urllib.quote(txt)

    @anon_only(lambda view: view.context.portal_url())
    def handle_request(self):
        """ redirect logged in users """

    def _create_member(self, targets=None, fields=None, confirmed=False):
        """
        tries to create a member object based on the request.

        returns the newly created member, or an error dictionary on failure.
        """
        factory = ICreateMembers(self.portal)

        self.errors = factory.validate(self.request.form)
        if self.errors:
            # XXX let's raise something instead of returning.
            # it's ugly to overload function return values to signal errors.
            return self.errors

        mem = factory.create(self.request.form)
        mem_name = mem.getFullname() or mem.getId()
        url = self._confirmation_url(mem)
        if utils.email_confirmation():
            if not confirmed:
                self._send_mail_to_pending_user(user_name=mem_name,
                                                email=self.request.get('email'),
                                                url=url)
            
                self.addPortalStatusMessage(_(u'psm_thankyou_for_joining',
                                              u'Thanks for joining ${portal_title}, ${mem_id}!<br/>\nA confirmation email has been sent to you with instructions on activating your account.',
                                              mapping={u'mem_id':mem.getId(),
                                                       u'portal_title':self.portal_title()}))
                portal_url = getToolByName(self.context, 'portal_url')()
                self.redirect(portal_url + '/message')
            return mem
        self.redirect(url)
        return mem

    create_member = action('join', apply=post_only(raise_=False))(_create_member)
    # the fact that we need to separate the decorated (user-facing) and undecorated methods here
    # suggests to me that we can refactor some functionality out of the view here. -egj

    @action('validate')
    def validate(self, targets=None, fields=None):
        """ this is really dumb. """

        #a special case for when the user has not yet entered a password confirmation:
        #pretend that they have
        if not self.request.form.get('confirm_password'):
            self.request.form['confirm_password'] = self.request.form.get('password', '')

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


class InviteJoinView(JoinView, ConfirmAccountView):
    """
    a preconfirmed join view that also introspects any invitation a
    prospective member has
    """

    template = ZopeTwoPageTemplateFile('invite-join.pt')

    truncate = staticmethod(truncate)

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
            imap = []
            invite = self.request.get('project')
            if invite in self.invites:
                project = self.context.projects.get(invite)
                if not project:
                    return tuple()
                from opencore.interfaces.workflow import IReadWorkflowPolicySupport
                closed =  IReadWorkflowPolicySupport(project).getCurrentPolicyId() == "closed_policy"
                imap.append(dict(id=invite, title=project.Title(),
                                 description=project.Description(),
                                 url=project.absolute_url(),
                                 logo=project.getLogo(),
                                 closed=closed))
            return imap
        return tuple()

    def validate_key(self):
        key = self.request.form.get('__k')
        if not key:
            raise zExceptions.BadRequest("Must present proper validation")
        if key != str(self.invites.key):
            raise ValueError('Bad confirmation key')
        return True

    @action('join', apply=post_only(raise_=False))
    def create_member(self, targets=None, fields=None):
        self.validate_key()
        # do all the member making stuff
        member = super(InviteJoinView, self)._create_member(targets, fields, confirmed=True)
        if isinstance(member, dict): # yuck
            # return errors 
            return member

        self.confirm(member)
        self.login(member.getId())
        auto_joined_list = self.do_invite_joins(member)
        go_to = ''
        if auto_joined_list:
            redirect_to_project = auto_joined_list[0]
            go_to = '?go_to=%s' % self.project_url(redirect_to_project)
        root = getToolByName(self.context, 'portal_url')()
        return self.redirect("%s/init-login%s" % (root, go_to))

    def do_invite_joins(self, member):
        """do the joins and activations"""
        mships = self.invite_util.convertInvitesForMember(member)
        auto_joined_list = []
        for mship in mships:
            mship._v_self_approved = True
            mship_id = mship.aq_parent.getId()
            if mship_id in self.proj_ids:
                mship.do_transition('approve_public')
                auto_joined_list.append(mship_id)
            notify(JoinedProjectEvent(mship))
        return auto_joined_list

    def project(self, _id):
        return self.context.projects.get(_id)

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
        root = getToolByName(self.context, 'portal_url')()
        if (not key) or (key != str(self.invites.key)):
            self.addPortalStatusMessage(_(u'psm_denied', u'Denied -- bad key'))
            return self.redirect("%s/%s" % (root, 'login'))
        
        member = self.is_pending(getEmail=self.email)
        if member:
            return self.redirect(self._confirmation_url(member))

        return None
