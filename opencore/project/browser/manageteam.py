from opencore.configuration import DEFAULT_ROLES, MEMBER_ROLES, ADMIN_ROLES
from Products.CMFCore.utils import getToolByName
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from Products.MailHost.MailHost import MailHostError
from Products.validation.validators.BaseValidators import EMAIL_RE
from opencore.nui.main.search import searchForPerson
from opencore.content.membership import OpenMembership
from opencore.interfaces.event import JoinedProjectEvent
from opencore.interfaces.event import LeftProjectEvent
from opencore.browser import formhandler
from opencore.account.utils import email_confirmation
from opencore.browser.base import view
from opencore.i18n import _
from opencore.utils import get_workflow_policy_config
from opencore.utility.interfaces import IEmailSender
from opencore.interfaces.message import ITransientMessage
from opencore.interfaces.membership import IEmailInvites
from opencore.project.browser.team import TeamRelatedView
from plone.memoize.view import memoize as req_memoize
from opencore.project.browser import mship_messages
from opencore.project.browser.base import ProjectBaseView
from opencore.account.browser import AccountView
from zope.component import getUtility
from zope.event import notify
import logging
import re
import urllib

log = logging.getLogger('opencore.project.manageteam')

EMAIL_RE = re.compile(EMAIL_RE)
TA_SPLIT = re.compile('\n|,')

@req_memoize
def _email_sender(view):
    portal = getToolByName(view.context, 'portal_url').getPortalObject()
    return IEmailSender(portal) #, mship_messages)

class ManageTeamView(TeamRelatedView, formhandler.OctopoLite, AccountView,
                     ProjectBaseView):
    """
    View class for the team management screens.
    """
    team_manage = ZopeTwoPageTemplateFile('team-manage.pt')
    team_manage_macros = ZopeTwoPageTemplateFile('team-manage-macros.pt')

    # XXX REFACTOR: role_map is repeated in nui.member.view.MemberAccountView
    # XXX could intefere with mbship tool b/c of aquisition
    rolemap = {'ProjectAdmin': 'administrator',
               'ProjectMember': 'member',
               }

    listedmap = {'public': 'yes',
                 'private': 'no',
                 }

    msg_category = 'membership'

    @property
    def template(self):
        """
        Team management
        """
        return self.team_manage

    def id_is_loggedin(self, item):
        id_ = None
        try: # @@HACK to get around admin user issues
            id_ = self.loggedinmember.getId()
        except 'MemberDataError':
            id_ = self.loggedinmember.id
        return item.get('id') == id_
        
    @property
    @req_memoize
    def pending_mships(self):
        cat = self.get_tool('portal_catalog')
        return cat(portal_type=OpenMembership.portal_type,
                   path=self.team_path,
                   review_state='pending',
                   )

    @property
    @req_memoize
    def pending_requests(self):
        pending = self.pending_mships
        return [b for b in pending if b.lastWorkflowActor == b.getId]

    @property
    @req_memoize
    def pending_invitations(self):
        pending = self.pending_mships
        return [b for b in pending if b.lastWorkflowActor != b.getId]

    @property
    @req_memoize
    def pending_email_invites(self):
        invites_util = getUtility(IEmailInvites, context=self.portal)
        invites = invites_util.getInvitesByProject(self.context.getId())
        return [{'id': urllib.quote(address), 'address': address,
                 'timestamp': timestamp}
                for address, timestamp in invites.items()]

    @property
    @req_memoize
    def active_mships(self):
        cat = self.get_tool('portal_catalog')
        mem_ids = self.team.getActiveMemberIds()
        brains = cat(portal_type=OpenMembership.portal_type,
                     path=self.team_path,
                     id=mem_ids)
        mships = []
        for brain in brains:
            data = self.getMshipInfoFromBrain(brain)
            mships.append(data)
        import operator
        
        return sorted(mships, key=operator.itemgetter('sortkey'))

    def getMshipInfoFromBrain(self, brain):
        """
        Return a formatted dictionary of information from a membership
        brain that is ready to be used by the templates.
        """
        try:
            member = self.get_tool('portal_memberdata')[brain.getId]
            Title = member.Title()
            sortkey = member.Title().lower()
        except KeyError:  # 'portal_owner' in tests, at least
            Title = brain.getId
            sortkey = brain.getId.lower()
            
        data = {'id': brain.id,
                'getId': brain.getId,
                'Title': Title,
                'sortkey': sortkey,
                }

        data['listed'] = self.listedmap[brain.review_state]
        data['active_since'] = brain.made_active_date

        role = self.team.getHighestTeamRoleForMember(brain.id)
        data['role'] = self.rolemap[role]
        data['role_value'] = role
        return data

    def getMemberURL(self, mem_id):
        mtool = self.get_tool('portal_membership')
        home_url = mtool.getHomeUrl(mem_id)
        if home_url:
            return '%s/profile' % home_url
        else:
            return None


    # XXX i kind of feel like this whole function is questionable    
    def doMshipWFAction(self, transition, mem_ids, pred=lambda mship:True):
        """
        Fires the specified workflow transition for the memberships
        associated with the specified member ids.

        o mem_ids: list of member ids for which to fire the
        transitions.  if this isn't provided, these will be obtained
        from the request object's 'member_ids' key.

        Returns the number of memberships for which the transition was
        successful.
        """
        team = self.team
        ids_acted_on = []
        for mem_id in mem_ids:
            mship = team._getOb(mem_id)
            if pred(mship):
                mship.do_transition(transition)
                ids_acted_on.append(mship.getId())
        return ids_acted_on

    def _getAccountURLForMember(self, mem_id):
        homeurl = self.membertool.getHomeUrl(mem_id)
        if homeurl is not None:
            return "%s/account" % homeurl

    @property
    @req_memoize
    def transient_msgs(self):
        return ITransientMessage(self.portal)

    def _add_transient_msg_for(self, mem_id, msg):
        # XXX not happy about generating the html for this here
        # but it's a one liner can move to a macro
        proj_url = self.context.absolute_url()
        title = self.context.title
        msg = '%(msg)s <a href="%(proj_url)s">%(title)s</a>' % locals()
        self.transient_msgs.store(mem_id, self.msg_category, msg)


    ##################
    #### MEMBERSHIP REQUEST BUTTON HANDLERS
    ##################

    @formhandler.action('approve-requests')
    def approve_requests(self, targets, fields=None):

        if not targets:
            self.add_status_message(_(u'psm_please_select_members', u'Please select members to approve.'))
            return {}

        mem_ids = targets
        wftool = self.get_tool('portal_workflow')
        team = self.team

        napproved = 0
        res = {}
        for mem_id in mem_ids:
            mship = team._getOb(mem_id)
            # approval transition has a different id for public and
            # private, have to look up by name
            transition = [t for t in wftool.getTransitionsFor(mship)
                          if t.get('name') == 'Approve']
            if not transition:
                continue
            transition_id = transition[0]['id']
            wftool.doActionFor(mship, transition_id)
            napproved += 1

            notify(JoinedProjectEvent(mship))

            mdtool = getToolByName(self.context, 'portal_memberdata')
            mdtoolpath = '/'.join(mdtool.getPhysicalPath())
            mem_path = '%s/%s' % (mdtoolpath, mem_id) 
            mem_metadata = self.catalog.getMetadataForUID(mem_path) 
            mem_user_name = mem_metadata['getFullname'] or mem_metadata['id']

            msg_subs = {
                'project_title': self.context.title,
                'user_name': mem_user_name,
                'project_noun': self.project_noun,
                'portal_url': self.portal.absolute_url(),
                'project_url': self.project_url(self.context.getId()),
                }

            #XXX sending the email should go in an event subscriber
            try:
                _email_sender(self).sendMail(
                    mem_id, msg=mship_messages.request_approved,
                    subject=mship_messages.request_approved_subject,
                    **msg_subs)
            except MailHostError: 
                pass
            self._add_transient_msg_for(mem_id, 'You have been accepted to')
            res[mem_id] = {'action': 'delete'}
            # will only be one mem_id in AJAX requests
            brain = self.catalog(path='/'.join(mship.getPhysicalPath()))[0]
            extra_context={'item': self.getMshipInfoFromBrain(brain),
                           'team_manage_macros': self.team_manage_macros.macros,
                           'changeable': True, # they're removable
                           }
            html = self.render_macro(self.team_manage_macros.macros['mshiprow'],
                                     extra_context=extra_context)
            res['mship-rows'] = {'action': 'append',
                                 'html': html,
                                 'effects':  'fadeIn'}

        if napproved == 1:
            self.add_status_message(_(u'psm_one_request_approved', u'You have added ${mem_id}.',
                                      mapping={u'mem_id':mem_id}))
        else:
            self.add_status_message(_(u'psm_many_requests_approved', u'You have added ${num_approved} members.'
                                      , mapping={u'num_approved':napproved}))
            
        if napproved:
            self.team.reindexTeamSpaceSecurity()

        return res

    @formhandler.action('discard-requests')
    def discard_requests(self, targets, fields=None):
        """
        Actually deletes the membership objects, doesn't send a
        notifier.

        Currently hidden in UI because it's confusing to have two
        options with no explanation.
        """
        if not targets:
            self.add_status_message(_(u'psm_select_members_discard',u'Please select members to discard.'))
            return {}

        # copy targets list b/c manage_delObjects empties the list

        mem_ids = targets[:]
        self.team.manage_delObjects(ids=mem_ids)
        plural = len(targets[:]) != 1
        msg = u"Request%s discarded: %s" % (plural and 's' or '',', '.join(targets[:]))
        
        self.add_status_message(msg)
        return dict( ((mem_id, {'action': 'delete'}) for mem_id in mem_ids) )

    @formhandler.action('reject-requests')
    def reject_requests(self, targets, fields=None):
        """
        Notifiers should be handled by workflow transition script.
        """
        if not targets:
            self.add_status_message(u'Please select members to deny.')
            return {}

        # copy targets list b/c manage_delObjects empties the list
        mem_ids = targets[:]
        self.doMshipWFAction('reject_by_admin', mem_ids)
        sender = _email_sender(self)

        for mem_id in mem_ids:
            mdtool = getToolByName(self.context, 'portal_memberdata')
            mdtoolpath = '/'.join(mdtool.getPhysicalPath())
            mem_path = '%s/%s' % (mdtoolpath, mem_id) 
            mem_metadata = self.catalog.getMetadataForUID(mem_path) 
            mem_user_name = mem_metadata['getFullname'] or mem_metadata['id']

            msg_subs = {
                'project_title': self.context.title,
                'user_name': mem_user_name,
                'project_noun': self.project_noun,                
                }
        
            msg = sender.constructMailMessage(mship_messages.request_denied,
                                              **msg_subs)
            msg_subject = sender.constructMailMessage(
                mship_messages.request_denied_subject,
                **msg_subs)
            sender.sendMail(mem_id, msg=msg, subject=msg_subject)
            self._add_transient_msg_for(mem_id, 'You have been denied membership to')

        plural = len(mem_ids) != 1
        msg = u"Request%s denied: %s" % (plural and 's' or '',', '.join(mem_ids))
        self.add_status_message(msg)
        return dict( ((mem_id, {'action': 'delete'}) for mem_id in mem_ids) )


    ##################
    #### MEMBERSHIP INVITATION BUTTON HANDLERS
    ##################

    @formhandler.action('remove-invitations')
    def remove_invitations(self, targets, fields=None):
        """
        Deletes (or deactivates, if there's history to preserve) the
        membership objects.  Should send notifiers.
        """
        mem_ids = targets
        wftool = self.get_tool('portal_workflow')
        pwft = getToolByName(self, 'portal_placeful_workflow')
        deletes = []
        sender = _email_sender(self)
        
        msg_subs = {
                'project_title': self.context.title,
                'project_noun': self.project_noun,
                }
        msg = sender.constructMailMessage(mship_messages.invitation_retracted,
                                          **msg_subs)
        msg_subject = sender.constructMailMessage(
            mship_messages.invitation_retracted_subject,
            **msg_subs)
        ret = {}
        for mem_id in mem_ids:
            mship = self.team.getMembershipByMemberId(mem_id)
            config = get_workflow_policy_config(self.team)
            if config is not None:
                wf_ids = config.getPlacefulChainFor('OpenMembership')
                wf_id = wf_ids[0]
            else:
                wf_id = 'openplans_team_membership_workflow'
            status = wftool.getStatusOf(wf_id, mship)
            if status.get('action') == 'reinvite':
                # deactivate
                wftool.doActionFor(mship, 'deactivate')
            else:
                # delete
                deletes.append(mem_id)
            ret[mem_id] = {'action': 'delete'}
            if email_confirmation():
                sender.sendMail(mem_id, msg=msg, subject=msg_subject)

        if deletes:
            self.team.manage_delObjects(ids=deletes)

        plural = len(mem_ids) != 1
        msg = u'Invitation%s removed: %s' % (plural and 's' or '', ', '.join(mem_ids))
        self.add_status_message(msg)
        return ret


    @formhandler.action('remind-invitations')
    def remind_invitations(self, targets, fields=None):
        """
        Sends an email reminder to the specified membership
        invitations.
        """
        mem_ids = targets
        project_title = self.context.title
        sender = _email_sender(self)
        for mem_id in mem_ids:
            acct_url = self._getAccountURLForMember(mem_id)
            mdtool = getToolByName(self.context, 'portal_memberdata')
            mdtoolpath = '/'.join(mdtool.getPhysicalPath())
            mem_path = '%s/%s' % (mdtoolpath, mem_id) 
            mem_metadata = self.catalog.getMetadataForUID(mem_path) 
            mem_user_name = mem_metadata['getFullname'] or mem_metadata['id']

            logged_in_mem = self.loggedinmember
            logged_in_mem_name = logged_in_mem.getFullname() or logged_in_mem.id

            msg_vars = {'project_title': project_title,
                        'user_name': mem_user_name,
                        'account_url': acct_url,
                        'inviter_name': logged_in_mem_name,
                        }

            if mem_metadata['review_state'] == 'pending':
                mem = mdtool.get(mem_id)
                msg_vars['conf_url'] = self._confirmation_url(mem)
                sender.sendMail(mem_id, 
                                msg=mship_messages.remind_pending_invitee,
                                subject=mship_messages.remind_pending_invitee_subject,
                                **msg_vars)
            else:
                sender.sendMail(mem_id, msg=mship_messages.remind_invitee,
                                subject=mship_messages.remind_invitee_subject,
                                **msg_vars)

        if not mem_ids:
            self.add_status_message(_(u"remind_invite_none_selected"))
        else:
            plural = len(mem_ids) != 1
            msg = "Reminder%s sent: %s" % (plural and 's' or '', ", ".join(mem_ids))
            self.add_status_message(msg)

        self.redirect(self.request.ACTUAL_URL)

    @formhandler.action('remove-email-invites')
    def remove_email_invites(self, targets, fields=None):
        """
        Retracts invitations sent to email addresses.  Should send
        notifiers.
        """
        addresses = [urllib.unquote(t).strip() for t in targets]

        sender = _email_sender(self)
        msg_subs = {
                'project_title': self.context.title,
                'project_noun': self.project_noun,
                }
        msg = sender.constructMailMessage(mship_messages.invitation_retracted,
                                          **msg_subs)
        msg_subject = sender.constructMailMessage(
            mship_messages.invitation_retracted_subject,
            **msg_subs)

        invite_util = getUtility(IEmailInvites, context=self.portal)
        proj_id = self.context.getId()
        for address in addresses:
            invite_util.removeInvitation(address, proj_id)
            if email_confirmation():
                sender.sendMail(address, msg=msg, subject=msg_subject)

        plural = len(addresses) != 1
        msg = u'Email invitation%s removed: %s' % (plural and 's' or '',', '.join(addresses))
        self.add_status_message(msg)

        ret = dict([(target, {'action': 'delete'}) for target in targets])
        return ret

    @req_memoize    
    def join_url(self, address, key, project):
        args = dict(email=address, project=project, __k=key)
        query_str = urllib.urlencode(args)
        portal_url = self.portal.absolute_url()
        url = "%s/invite-join?%s" % (portal_url, query_str)
        return url

    def mship_only_admin(self, mship):
        mem_id = mship.getId()
        path = mship.getPhysicalPath()
        proj_id = path[-2]
        return not self._is_only_admin(proj_id, mem_id)

    #XXX lifted directly from nui.member.MemberAccountView
    # should pull into common place
    def _is_only_admin(self, proj_id, mem_id=None):
        team = self.get_tool('portal_teams')._getOb(proj_id)

        # for some reason checking the role is not enough
        # I've gotten ProjectAdmin roles back for a member
        # in the pending state
        ## XXX this is because role is independent of state,
        #      and we haven't been changing the role when we
        #      transition to a new state. can probably remove
        #      now that this is changing, but maybe best to
        #      keep this just in case.
        if mem_id is None:
            mem_id = self.viewed_member_info['id']
        mship = team._getOb(mem_id)
        wft = self.get_tool('portal_workflow')
        review_state = wft.getInfoFor(mship, 'review_state')
        if review_state not in self.active_states: return False

        role = team.getHighestTeamRoleForMember(mem_id)
        if role != 'ProjectAdmin': return False

        portal_path = '/'.join(self.portal.getPhysicalPath())
        team_path = '/'.join([portal_path, 'portal_teams', proj_id])
        project_admins = self.catalog(
            highestTeamRole='ProjectAdmin',
            portal_type='OpenMembership',
            review_state=self.active_states,
            path=team_path,
            )

        return len(project_admins) <= 1


    ##################
    #### ACTIVE MEMBERSHIP BUTTON HANDLERS
    ##################

    @formhandler.action('remove-members')
    def remove_members(self, targets, fields=None):
        """
        Doesn't actually remove the membership objects, just
        puts them into an inactive workflow state.
        """
        mem_ids = targets
        mems_removed = self.doMshipWFAction('deactivate', mem_ids, self.mship_only_admin)
        sender = _email_sender(self)
        ret = {}
        #XXX sending an email should be in an event handler
        for mem_id in mems_removed:
            mship = self.team._getOb(mem_id)
            notify(LeftProjectEvent(mship))

            mdtool = getToolByName(self.context, 'portal_memberdata')
            mdtoolpath = '/'.join(mdtool.getPhysicalPath())
            mem_path = '%s/%s' % (mdtoolpath, mem_id) 
            try:
                mem_metadata = self.catalog.getMetadataForUID(mem_path) 
                mem_user_name = mem_metadata['getFullname'] or mem_metadata['id']
            except KeyError:
                mem_user_name = mem_id

            msg_subs = {
                'project_title': self.context.title,
                'user_name': mem_user_name,
                'project_noun':self.project_noun,
                }
            
            try:
                sender.sendMail(mem_id,
                                msg=mship_messages.membership_deactivated,
                                subject=mship_messages.membership_deactivated_subject,
                                **msg_subs)
            except MailHostError:
                self.add_status_message(_(u'psm_error_sending_mail_to_member', 'Error sending mail to: ${mem_id}', mapping={u'mem_id': mem_id}))
            self._add_transient_msg_for(mem_id, 'You have been deactivated from')
            ret[mem_id] = {'action': 'delete'}

        if mems_removed:
            plural = len(mems_removed) != 1
            msg = "Member%s deactivated: %s" % (plural and 's' or '', ', '.join(mems_removed))
        elif mem_ids:
            msg = 'Cannot remove last admin: %s' % mem_ids[0]
        else:
            msg = 'Please select members to remove.'
        self.add_status_message(msg)

        self.team.reindexTeamSpaceSecurity()
        return ret

    @formhandler.action('promote-admin')
    def promote_admin(self, targets, fields=None):
        mem_ids = targets
        changes = []
        team = self.team

        for mem_id in mem_ids:
            if team.getHighestTeamRoleForMember(mem_id) == 'ProjectAdmin':
                continue
            team.setTeamRolesForMember(mem_id, ADMIN_ROLES)
            changes.append(mem_id)

        self.team.reindexTeamSpaceSecurity()

        if len(changes) == 0:
            msg = u"Select one or more project members to promote to admins"
            self.add_status_message(msg)
            return self.redirect('%s/manage-team' % self.context.absolute_url())

        for mem_id in changes:
            transient_msg = 'You are now an admin of'
            self._add_transient_msg_for(mem_id, transient_msg)

            status_msg = _(u'promote_to_admin',
                           mapping={'name': mem_id})
            self.add_status_message(status_msg)

        return self.redirect('%s/manage-team' % self.context.absolute_url())

    @formhandler.action('demote-admin')
    def demote_admin(self, targets, fields=None):
        mem_ids = targets
        changes = []
        team = self.team

        for mem_id in mem_ids:
            if team.getHighestTeamRoleForMember(mem_id) == 'ProjectMember':
                continue
            team.setTeamRolesForMember(mem_id, MEMBER_ROLES)
            changes.append(mem_id)

        self.team.reindexTeamSpaceSecurity()

        if len(changes) == 0:
            msg = u"Select one or more project admins to demote to members"
            self.add_status_message(msg)
            return self.redirect('%s/manage-team' % self.context.absolute_url())

        for mem_id in changes:
            transient_msg = 'You are no longer an admin of'
            self._add_transient_msg_for(mem_id, transient_msg)

            status_msg = _(u'demote_to_member',
                           mapping={'name': mem_id})
            self.add_status_message(status_msg)

        return self.redirect('%s/manage-team' % self.context.absolute_url())


    ##################
    #### MEMBER SEARCH BUTTON HANDLER
    ##################

    # XXX this method has always been very slow (subjective impression)
    #     .. not sure why, but there are a few obvious improvements that
    #        could be made. should profile this, though. -egj
    @formhandler.action('search-members')
    def search_members(self, targets=None, fields=None):
        """
        Performs the catalog query and then puts the results in an
        attribute on the view object for use by the template.  Filters
        out any members for which a team membership already exists,
        since this is used to add new members to the team.
        """
        filtered_states = ('pending', 'private', 'public')
        existing_ids = self.team.getMemberIdsByStates(filtered_states)

        existing_ids = dict.fromkeys(existing_ids) # XXX why on earth..? -egj
        # XXX TODO: it should just be easier to get these casually, really
        self.existing_ids = dict.fromkeys(existing_ids)

        search_for = self.request.form.get('search_for')
        if not search_for:
            self.add_status_message(u'Please enter search text.')
            return

        # XXX searchForPerson seems excessive here, why not just a catalog query? -egj
        results = searchForPerson(self.membranetool, search_for)

        self.results = results
        if not len(results):
            self.add_status_message(u'No members were found.')

        
    ##################
    #### MEMBER ADD BUTTON HANDLER
    ##################

    def _doInviteMember(self, mem_id):
        """
        Perform the actual membership invitation, either by creating a
        membership object or firing the reinvite transition.
        """
        if not mem_id in self.team.getMemberIds():
            # create the membership
            self.team.addMember(mem_id, reindex=False)
        else:
            # reinvite existing membership
            wftool = self.get_tool('portal_workflow')
            mship = self.team.getMembershipByMemberId(mem_id)
            transitions = wftool.getTransitionsFor(mship)
            if 'reinvite' not in [t['id'] for t in transitions]:
                return False
            wftool.doActionFor(mship, 'reinvite')
        return True

    @formhandler.action('invite-member')
    def invite_member(self, targets, fields=None):
        """
        Sends an invitation notice, and creates a pending membership
        object (or puts the existing member object into the pending
        state).  The member id is specified in the request form, as
        the value for the 'invite-member' button.
        """

        mem_id = targets[0] # should only be one
        if not self._doInviteMember(mem_id):
            # XXX when does this happen?
            self.add_status_message(u'You cannot reinvite %s to join this %s yet.' % (mem_id, self.project_noun))
            self.redirect('%s/manage-team' % self.context.absolute_url())

        acct_url = self._getAccountURLForMember(mem_id)
        logged_in_mem = self.loggedinmember
        logged_in_mem_name = logged_in_mem.getFullname() or logged_in_mem.id

        mdtool = getToolByName(self.context, 'portal_memberdata')
        mdtoolpath = '/'.join(mdtool.getPhysicalPath())
        mem_path = '%s/%s' % (mdtoolpath, mem_id) 
        mem_metadata = self.catalog.getMetadataForUID(mem_path) 
        mem_user_name = mem_metadata['getFullname'] or mem_metadata['id']

        # XXX if member hasn't logged in yet, acct_url will be whack
        msg_subs = {
            'project_title': self.context.title,
            'account_url': acct_url,
            'user_name': mem_user_name,
            'inviter_name': logged_in_mem_name,
            'portal_name': self.portal.title,
            'portal_url': self.portal.absolute_url(),
            }
        
        self.send_invite_member_email(mem_id, msg_subs)
        self.add_status_message(u'You invited %s to join this %s' % (mem_id, self.project_noun))
        self.redirect('manage-team')
        
    def send_invite_member_email(self, mem_id, msg_subs):
        _email_sender(self).sendMail(mem_id, 
                                     msg=mship_messages.invite_member,
                                     subject=mship_messages.invite_member_subject,
                                     **msg_subs)

    @view.memoizedproperty
    def invite_util(self):
        return getUtility(IEmailInvites)

    @formhandler.action('remind-email-invites')
    def remind_email_invites(self, targets, fields=None):
        if not targets:
            self.add_status_message(_(u"remind_invite_none_selected"))
        else:
            self.redirect("invite?remind=True&email-invites=%s" % ",".join(targets))

        
class InviteView(ManageTeamView):
    ##################
    #### EMAIL INVITATION BUTTON HANDLERS
    ##################

    template = ZopeTwoPageTemplateFile('invite-with-message.pt')

    ##################
    #### EMAIL INVITES BUTTON HANDLER
    ##################

    @property
    def email_invites(self):
        return [invite.strip() for invite \
                in TA_SPLIT.split(self.request.form.get('email-invites')) if len(invite.strip())>0]

    def validate_email_invites(self, invites):
        bad = []
        for addy in invites:
            if addy: # ignore empty entries
                if EMAIL_RE.match(addy) is None:
                    bad.append(addy)
        return bad

    def do_nonmember_invitation_email(self, addy, proj_id):
        # perform invitation

        key = self.invite_util.addInvitation(addy, proj_id)
        msg_subs = dict(join_url=self.join_url(addy, key, proj_id),
                        #FIXME: spam-check this
                        user_message=self.request.get('message', ''), 
                        subject=self.request.get('subject', ''),
                        project_title=self.context.Title(),
                        project_noun=self.project_noun,
                        site_contact_url=self.portal.absolute_url() + "/contact-site-admin",
                        )

        if email_confirmation():
            _email_sender(self).sendMail(
                addy, msg=mship_messages.email_invite_static_body,
                mfrom=self.loggedinmember.id, **msg_subs)
        else:
            msg = _email_sender(self).constructMailMessage(
                mship_messages.email_invite_static_body, **msg_subs)
            log.info(msg)
        return key

    def invite_email_boiler(self):
        # this is a hack to massage the email_invite_static_body text
        # to look good on the screen for presentation purposes; it is
        # used in its virgin form in the email
        msg_subs = dict(user_message='',
                        join_url=self.join_url('', '', ''),
                        portal_title=self.portal_title(),
                        project_noun=self.project_noun,
                        site_contact_url=self.portal.absolute_url() + "/contact-site-admin",
                        )
        
        msg = (self.translate(_(u'email_invite_static_body', mapping=msg_subs)))
        msg = msg.replace('\n\n', '<br>')
        msg = msg.replace('\n', '<br>')
        return msg


    @formhandler.action('remind-email-invites')
    def remind_email_invites(self, targets=None, fields=None):
        """
        Sends an email reminder to the specified email invitees.
        """
        # perform reminder
        invites = self.request.get('email-invites').split(",")
        addresses = [urllib.unquote(t).strip() for t in invites]

        sender = _email_sender(self)
        project_title = self.context.Title()
        proj_id = self.context.getId()
        for address in addresses:
            key = self.invite_util.getInvitesByEmailAddress(address).key
            msg_subs = dict(join_url=self.join_url(address, key, proj_id),
                            #FIXME: spam-check this
                            user_message=self.request.get('message', ''), 
                            subject=self.request.get('subject', ''),
                            project_title=self.context.Title(),
                            project_noun=self.project_noun,
                            site_contact_url=self.portal.absolute_url() + "/contact-site-admin",
                            )

            msg = sender.constructMailMessage(
                mship_messages.email_invite_static_body,
                mfrom=self.loggedinmember.id, **msg_subs)
            if email_confirmation():
                sender.sendMail(address, msg=msg)
            else:
                log.info(msg)

        plural = len(addresses) != 1

        msg = "Reminder%s sent: %s" % (plural and 's' or '',', '.join(addresses))
        self.add_status_message(msg)
        self.redirect('manage-team')

        
    @formhandler.action('email-invites')
    def add_email_invites(self, targets=None, fields=None):
        invites = self.email_invites

        psm = self._add_email_invites(invites)
        if not psm:
            return
        if psm['mem_invites']:
            self.add_status_message(u"Members invited: %s"
                                        % ', '.join(psm['mem_invites']))
        if psm['mem_failures']:
            self.add_status_message(u"Members for whom invitation failed: %s"
                                        % ', '.join(psm['mem_failures']))
        if psm['already_invited']:
            self.add_status_message(u"Emails already invited: %s"
                                        % ', '.join(psm['already_invited']))
        if psm['email_invites']:
            self.add_status_message(u"Email invitations: %s"
                                        % ', '.join(psm['email_invites']))
        if psm['mem_already_member']:
            if len(psm['mem_already_member']) > 1:
                self.add_status_message(u"%s are already members of this project."
                                        % ', '.join(psm['mem_already_member']))
            else:
                self.add_status_message(u"%s is already a member of this project."
                                        % ', '.join(psm['mem_already_member']))
        self._norender = True
        self.redirect('manage-team')
        
    def _add_email_invites(self, invites):
        """
        Invite non-site-members to join the site and this project.
        Sends an email to the address, records the action so they'll
        be automatically added to this project upon joining the site.

        If the email address is already that of a site member, then
        that member will be invited to join the project, as per usual.

        Email addresses are in the 'email-invites' form field.  If any
        of them fail validation as an email address then an error is
        returned and the entire operation is aborted.
        """

        bad = self.validate_email_invites(invites)
        if bad:
            plural = len(bad) != 1
            try:
                psm = (u"Poorly formed email address%s, please correct: %s"
                       % (plural and 'es' or '', ', '.join(bad)))
            except UnicodeDecodeError:
                portal_url = getToolByName(self.context, 'portal_url')()
                contact_link = '<a href="%s/contact-site-admin">contact</a>' % portal_url
                psm = (u"An invalid email address was entered. If you believe this is incorrect, please %s us"
                       % contact_link)
            self.add_status_message(psm)
            return # don't do anything, just re-render the form

        proj_id = self.context.getId()
        proj_title = self.context.title
        mbtool = self.membranetool
        uSR = mbtool.unrestrictedSearchResults
        mem_invites = []
        mem_failures = []
        mem_already_member = []
        email_invites = []
        already_invited = []

        for addy in invites:
            # first check to see if we're already a site member
            addy = addy.strip()
            if not addy:
                continue

            match = uSR(getEmail=addy)
            if match:
                # member already has this address
                brain = match[0]
                mem_id = brain.getId
                invited = self._doInviteMember(mem_id)
                if invited:
                    acct_url = self._getAccountURLForMember(mem_id)

                    logged_in_mem = self.loggedinmember
                    logged_in_mem_name = logged_in_mem.getFullname() or logged_in_mem.id

                    mdtool = getToolByName(self.context, 'portal_memberdata')
                    mdtoolpath = '/'.join(mdtool.getPhysicalPath())
                    mem_path = '%s/%s' % (mdtoolpath, mem_id) 
                    mem_metadata = self.catalog.getMetadataForUID(mem_path) 
                    mem_user_name = mem_metadata['getFullname'] or mem_metadata['id']

                    msg_subs = {
                        'project_title': proj_title,
                        'account_url': acct_url,
                        'user_name': mem_user_name,
                        'inviter_name': logged_in_mem_name,
                        'portal_name': self.portal.title,
                        'portal_url': self.portal.absolute_url(),
                        }

                    if email_confirmation():
                        if mem_metadata['review_state'] == 'pending':
                            mem = mdtool.get(mem_id)
                            msg_subs['conf_url'] = self._confirmation_url(mem)
                            _email_sender(self).sendMail(
                                mem_id,
                                msg=mship_messages.invite_pending_member,
                                subject=mship_messages.invite_pending_member_subject,
                                **msg_subs)
                        else:
                            _email_sender(self).sendMail(
                                mem_id,
                                msg=mship_messages.invite_member,
                                subject=mship_messages.invite_member_subject,
                                **msg_subs)
                    mem_invites.append(mem_id)
                else:
                    # invitation attempt failed
                    if mem_id not in self.context.projectMemberIds():
                        mem_failures.append(mem_id)
                    else:
                        mem_already_member.append(mem_id)
            else:
                # not a member
                if addy in self.invite_util.getInvitesByProject(proj_id):
                    already_invited.append(addy)
                else:
                    self.do_nonmember_invitation_email(addy, proj_id)
                    email_invites.append(addy)
                    
        return dict(mem_invites=mem_invites,
                    mem_failures=mem_failures,
                    email_invites=email_invites,
                    already_invited=already_invited,
                    mem_already_member=mem_already_member)


class InviteMemberCustomView(ManageTeamView):
    template = ZopeTwoPageTemplateFile('invite-member.pt')
    
    def send_invite_member_email(self, mem_id, msg_subs):
        message = self.request.form.get('message')
        subject = self.request.form.get('subject')
        _email_sender(self).sendMail(mem_id, msg=message, subject=subject)

