from opencore.configuration import DEFAULT_ROLES
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
from opencore.browser.base import _
from opencore.browser.base import view
from opencore.nui.email_sender import EmailSender
from opencore.interfaces.message import ITransientMessage
from opencore.interfaces.membership import IEmailInvites
from opencore.project.browser.team import TeamRelatedView
from plone.memoize.view import memoize as req_memoize
from opencore.project.browser import mship_messages
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
    return EmailSender(view, mship_messages)

class ManageTeamView(TeamRelatedView, formhandler.OctopoLite):
    """
    View class for the team management screens.
    """
    team_manage = ZopeTwoPageTemplateFile('team-manage.pt')
    team_manage_blank = ZopeTwoPageTemplateFile('team-manage-blank.pt')
    team_manage_macros = ZopeTwoPageTemplateFile('team-manage-macros.pt')

    mship_type = OpenMembership.portal_type

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
        Different template for brand new teams, before any members are added.

        XXX Deferred until immediately after the initial NUI launch.
        """
        #mem_ids = self.team.getMemberIds()
        #if getattr(self, '_norender', None):
        #    return
        #if len(mem_ids) == 1:
        #    # the one team member is most likely the project creator
        #    return self.team_manage_blank
        #return self.team_manage

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
        return cat(portal_type=self.mship_type,
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
        brains = cat(portal_type=self.mship_type,
                     path=self.team_path,
                     id=mem_ids)
        mships = []
        for brain in brains:
            data = self.getMshipInfoFromBrain(brain)
            mships.append(data)
        return mships

    def getMshipInfoFromBrain(self, brain):
        """
        Return a formatted dictionary of information from a membership
        brain that is ready to be used by the templates.
        """
        data = {'id': brain.id,
                'getId': brain.getId,
                }

        data['listed'] = self.listedmap[brain.review_state]
        data['active_since'] = brain.made_active_date

        role = self.team.getHighestTeamRoleForMember(brain.id)
        data['role'] = self.rolemap[role]
        data['role_value'] = role
        return data

    def getMemberURL(self, mem_id):
        mtool = self.get_tool('portal_membership')
        return '%s/profile' % mtool.getHomeUrl(mem_id)

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
            self.add_status_message(u'Please select members to approve.')
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

            #XXX sending the email should go in an event subscriber
            try:
                _email_sender(self).sendEmail(mem_id, msg_id='request_approved',
                                            project_title=self.context.title,
                                            project_url=self.context.absolute_url())
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
            self.add_status_message(u'You have added %s.' % mem_id)
        else:
            self.add_status_message(u'You have added %d members.' % napproved)
            
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
            self.add_status_message(u'Please select members to discard.')
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
        msg = sender.constructMailMessage('request_denied',
                                          project_title=self.context.title)
        for mem_id in mem_ids:
            sender.sendEmail(mem_id, msg=msg)
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
        msg = sender.constructMailMessage('invitation_retracted',
                                          project_title=self.context.title)
        ret = {}
        for mem_id in mem_ids:
            mship = self.team.getMembershipByMemberId(mem_id)
            config = pwft.getWorkflowPolicyConfig(mship)
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
                sender.sendEmail(mem_id, msg=msg)

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
            # XXX if member hasn't logged in yet, acct_url will be whack
            #     probably okay b/c account creation auto-logs you in
            msg_vars = {'project_title': project_title,
                        'account_url': acct_url,
                        }
            sender.sendEmail(mem_id, msg_id='remind_invitee', **msg_vars)

        if not mem_ids:
            self.addPortalStatusMessage(_(u"remind_invite_none_selected"))
        else:
            plural = len(mem_ids) != 1
            msg = "Reminder%s sent: %s" % (plural and 's' or '', ", ".join(mem_ids))
            self.add_status_message(msg)

    @formhandler.action('remove-email-invites')
    def remove_email_invites(self, targets, fields=None):
        """
        Retracts invitations sent to email addresses.  Should send
        notifiers.
        """
        addresses = [urllib.unquote(t) for t in targets]

        sender = _email_sender(self)
        msg = sender.constructMailMessage('invitation_retracted',
                                          project_title=self.context.title)

        invite_util = getUtility(IEmailInvites, context=self.portal)
        proj_id = self.context.getId()
        for address in addresses:
            invite_util.removeInvitation(address, proj_id)
            if email_confirmation():
                sender.sendEmail(address, msg=msg)

        plural = len(addresses) != 1
        msg = u'Email invitation%s removed: %s' % (plural and 's' or '',', '.join(addresses))
        self.add_status_message(msg)

        ret = dict([(target, {'action': 'delete'}) for target in targets])
        return ret

    @req_memoize    
    def join_url(self, address):
        # XXX if member hasn't logged in yet, acct_url will be whack
        key = self.invite_util.getInvitesByEmailAddress(address).key
        query_str = urllib.urlencode(dict(email=address,__k=key))
        #query_str = urllib.urlencode({'email': address})
        join_url = "%s/invite-join?%s" % (self.portal.absolute_url(),
                                          query_str)
        return join_url

    @formhandler.action('remind-email-invites')
    def remind_email_invites(self, targets, fields=None):
        """
        Sends an email reminder to the specified email invitees.
        """
        addresses = [urllib.unquote(t) for t in targets]
        sender = _email_sender(self)
        project_title = self.context.title
        for address in addresses:
            msg_subs = dict(project_title=self.context.title,
                            join_url=self.join_url(address),
                            portal_url=self.siteURL,
                            portal_title=self.portal_title()
                            )
            
            sender.sendEmail(address, msg_id='invite_email', **msg_subs)

        plural = len(addresses) != 1

        msg = "Reminder%s sent: %s" % (plural and 's' or '',', '.join(addresses))
        self.add_status_message(msg)

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
        project_admins = self.catalogtool(
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
            try:
                sender.sendEmail(mem_id, msg_id='membership_deactivated',
                                 project_title=self.context.title)
            except MailHostError:
                self.add_status_message('Error sending mail to: %s' % mem_id)
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

    @formhandler.action('set-roles')
    def set_roles(self, targets, fields):
        """
        Brings the stored team roles into sync with the values stored
        in the request form.
        """
        roles = [f.get('role') for f in fields]
        roles_from_form = dict(zip(targets, roles))

        team = self.team
        changes = []
        for mem_id in roles_from_form:
            from_form = roles_from_form[mem_id]
            if team.getHighestTeamRoleForMember(mem_id) != from_form:
                index = DEFAULT_ROLES.index(from_form)
                mem_roles = DEFAULT_ROLES[:index + 1]
                team.setTeamRolesForMember(mem_id, mem_roles)
                changes.append(mem_id)

        if changes:
            commands = {}
            active_mships = self.active_mships
            active_mships = dict([(m['getId'], m) for m in active_mships])
            for mem_id in changes:
                item = active_mships.get(mem_id)
                if item:
                    extra_context={'item': item,
                                   'team_manage_macros': self.team_manage_macros,
                                   'changeable': True}
                    html = self.render_macro(self.team_manage_macros.macros['mshiprow'],
                                             extra_context=extra_context)
                    commands[mem_id] = {'action': 'replace',
                                        'html': html,
                                        'effects': 'highlight'}
                    promoted = team.getHighestTeamRoleForMember(mem_id) == 'ProjectAdmin'
                    if promoted:
                        transient_msg = 'You are now an admin of'
                        status_msg = _(u'promote_to_admin',
                                       mapping={'name': mem_id})
                    else:
                        transient_msg = 'You are no longer an admin of'
                        status_msg = _(u'demote_to_member',
                                       mapping={'name': mem_id})
                    self._add_transient_msg_for(mem_id, transient_msg)
                    self.add_status_message(status_msg)

            return commands
        else:
            msg = u"No roles changed"
            self.add_status_message(msg)
        

    ##################
    #### MEMBER SEARCH BUTTON HANDLER
    ##################

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
        existing_ids = dict.fromkeys(existing_ids)

        search_for = self.request.form.get('search_for')
        if not search_for:
            self.add_status_message(u'Please enter search text.')
            return
        results = searchForPerson(self.membranetool, search_for)
        results = [r for r in results if r.getId not in existing_ids]
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
            self.add_status_message(u'You cannot reinvite %s to join this project yet.' % mem_id)
            raise Redirect('%s/manage-team' % self.context.absolute_url())

        acct_url = self._getAccountURLForMember(mem_id)
        logged_in_mem = self.loggedinmember
        logged_in_mem_name = logged_in_mem.getFullname() or logged_in_mem.id

        mdtool = getToolByName(self.context, 'portal_memberdata')
        mdtoolpath = '/'.join(mdtool.getPhysicalPath())
        mem_path = '%s/%s' % (mdtoolpath, mem_id) 
        mem_metadata = self.catalogtool.getMetadataForUID(mem_path) 
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
        _email_sender(self).sendEmail(mem_id, msg_id='invite_member',
                                    **msg_subs)
        self.add_status_message(u'You invited %s to join this project.' % mem_id)

    @view.memoizedproperty
    def invite_util(self):
        return getUtility(IEmailInvites)
        
class InviteView(ManageTeamView):
    ##################
    #### EMAIL INVITATION BUTTON HANDLERS
    ##################
    invite_with_message = ZopeTwoPageTemplateFile('invite-with-message.pt')

    @property
    def template(self):
        return self.invite_with_message

    ##################
    #### EMAIL INVITES BUTTON HANDLER
    ##################

    @property
    def email_invites(self):
        return [invite.strip() for invite \
                in TA_SPLIT.split(self.request.form.get('email-invites'))]

    def validate_email_invites(self, invites):
        bad = []
        for addy in invites:
            if addy: # ignore empty entries
                if EMAIL_RE.match(addy) is None:
                    bad.append(addy)
        return bad

    def do_nonmember_invitation_email(self, addy, proj_id):
        # perform invitation
        msg_subs = dict(join_url=self.join_url(addy),
                        #FIXME: spam-check this
                        user_message=self.request.get('message', ''), 
                        subject=self.request.get('subject', ''),
                        project_title=self.context.Title(),
                        site_contact_url=self.portal.absolute_url() + "/contact-site-admin",
                        
                        )
        if email_confirmation():
            _email_sender(self).sendEmail(addy, msg_id='email_invite_static_body',
                                        **msg_subs)
        else:
            msg = _email_sender(self).constructMailMessage(msg_id='email_invite_static_body',
                                                         **msg_subs)
            log.info(msg)


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
        self._norender = True
        self.redirect(self.request.ACTUAL_URL) # redirect clears form values
        
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
            psm = (u"Poorly formed email address%s, please correct: %s"
                   % (plural and 'es' or '', ', '.join(bad)))
            self.add_status_message(psm)
            return # don't do anything, just re-render the form
        
        proj_id = self.context.getId()
        proj_title = self.context.title
        mbtool = self.membranetool
        uSR = mbtool.unrestrictedSearchResults
        mem_invites = []
        mem_failures = []
        email_invites = []
        already_invited = []
        for addy in invites:
            # first check to see if we're already a site member
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
                    mem_metadata = self.catalogtool.getMetadataForUID(mem_path) 
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
                        _email_sender(self).sendEmail(mem_id,
                                                    msg_id='invite_member',
                                                    **msg_subs)
                    mem_invites.append(mem_id)
                else:
                    # invitation attempt failed
                    mem_failures.append(mem_id)
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
                    already_invited=already_invited)


