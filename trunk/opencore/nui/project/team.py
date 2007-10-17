from Products.CMFCore.utils import getToolByName
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from Products.MailHost.MailHost import MailHostError
from Products.validation.validators.BaseValidators import EMAIL_RE
from opencore.configuration import DEFAULT_ROLES
from opencore.content.membership import OpenMembership
from opencore.nui import formhandler
from opencore.nui.email_sender import EmailSender
from opencore.nui.main import SearchView
from opencore.nui.main.search import searchForPerson
from opencore.nui.member.interfaces import ITransientMessage
from opencore.nui.project import mship_messages
from opencore.nui.project.interfaces import IEmailInvites
from operator import attrgetter
from plone.memoize.instance import memoize, memoizedproperty
from plone.memoize.view import memoize as req_memoize
from plone.memoize.view import memoize_contextless
from topp.utils.detag import detag
from zope.component import getUtility
from zope.i18nmessageid import Message
import re
import urllib


class TeamRelatedView(SearchView):
    """
    Base class for views on the project that are actually related to
    the team and team memberships.
    """
    def __init__(self, context, request):
        SearchView.__init__(self, context, request)
        project = self.context
        teams = project.getTeams()
        assert len(teams) == 1
        self.team = team = teams[0]
        self.team_path = '/'.join(team.getPhysicalPath())
        self.active_states = team.getActiveStates()
        self.sort_by = None


class RequestMembershipView(TeamRelatedView, formhandler.OctopoLite):
    """
    View class to handle join project requests.
    """
    template = ZopeTwoPageTemplateFile('request-membership.pt')

    def __call__(self):
        """ if already logged in / member of project, redirect appropriately """
        # if not logged in, redirect to the login form
        if not self.loggedin:
            self.add_status_message(msgid='please_sign_in')
            self.redirect('%s/login?came_from=%s' % (self.siteURL, self.request.ACTUAL_URL))
            return
        # if already a part of the team, redirect to project home page
        if self.member_info['id'] in self.team.getActiveMemberIds():
            self.add_status_message(msgid='already_project_member',
                                        default='You are already a member of this project.')
            self.redirect('%s?came_from=%s' % (self.context.absolute_url(), self.request.ACTUAL_URL))
        return super(RequestMembershipView, self).__call__()

    @formhandler.action('request-membership')
    def request_membership(self, targets=None, fields=None):
        """
        Delegates to the team object and handles destination.
        """
        if self.loggedin:
            joined = self.team.join()
        else:
            self.add_status_message(msgid='please_sign_in')
            self.redirect('%s/login?came_from=%s' % (self.siteURL, self.request.ACTUAL_URL))
            return

        if joined:
            team_manage_url = "%s/manage-team" % self.context.absolute_url()
            email_vars = {'member_id': self.member_info.get('id'),
                          'project_title': self.context.title,
                          'team_manage_url': team_manage_url,
                          }
            sender = EmailSender(self, mship_messages)
            email_msg = sender.constructMailMessage('membership_requested',
                                                    **email_vars)
            request_message = self.request.form.get('request-message')
            if request_message:
                # adding the two Message objects together creates a unicode
                # type, must instantiate a new Message
                email_msg += sender.constructMailMessage('mship_request_message')
                email_vars.update(member_message=detag(request_message))
                email_msg = Message(email_msg, mapping=email_vars)

            mto = self.team.get_admin_ids()

            for recipient in mto:
                try:
                    sender.sendEmail(recipient, msg=email_msg, **email_vars)
                except MailHostError:
                    pass
            psmid = 'proj_join_request_sent'
        else:
            psmid = 'already_proj_member'

        self.add_status_message(msgid=psmid,
                                mapping={'project_title':
                                         self.context.Title()}
                                    )
        self.template = None # don't render the form before the redirect
        self.redirect(self.context.absolute_url())


class ProjectTeamView(TeamRelatedView):

    admin_role = DEFAULT_ROLES[-1]

   
    @formhandler.button('sort')
    def handle_request(self):
        # this is what controls which sort method gets dispatched to
        # in the memberships property
        self.sort_by = self.request.form.get('sort_by', None)

    def handle_sort_membership_date(self):
        query = dict(portal_type='OpenMembership',
                 path=self.team_path,
                 review_state=self.active_states,
                 sort_on='made_active_date',
                 sort_order='descending',
                 )

        membership_brains = self.catalog(**query)
        # XXX for some reason, the descending sort is not working properly
        # seems to only want to be ascending
        # so let's just use python sort to sort the results ourselves
        membership_brains = sorted(
            membership_brains,
            key=attrgetter('made_active_date'),
            reverse=True)

        mem_ids = [b.getId for b in membership_brains]
        
        query = dict(portal_type='OpenMember',
                     getId=mem_ids,
                     )
        member_brains = self.membranetool(**query)
        lookup_dict = dict((b.getId, b) for b in member_brains if b.getId)
        batch_dict = [lookup_dict.get(b.getId) for b in membership_brains]
        batch_dict = filter(None, batch_dict)
        return self._get_batch(batch_dict, self.request.get('b_start', 0))

    def handle_sort_location(self):
        query = dict(portal_type='OpenMembership',
                 path=self.team_path,
                 review_state=self.active_states,
                 )
        mem_brains = self.catalog(**query)
        mem_ids = [mem_brain.getId for mem_brain in mem_brains]
        query = dict(sort_on='sortableLocation',
                     getId=mem_ids,
                     )
        # XXX these are member brains, not membership brains
        results = self.membranetool(**query)
        # XXX sort manually here, because it doesn't look like the catalog
        # has the ability to sort on multiple fields
        def sort_location_then_name(x, y):
            xloc, yloc = x.getLocation.lower(), y.getLocation.lower()
            if xloc < yloc: return -1
            if yloc < xloc: return 1
            return cmp(x.getId.lower(), y.getId.lower())

        results = sorted(results, cmp=sort_location_then_name)
        
        return self._get_batch(results, self.request.get('b_start', 0))

    def handle_sort_contributions(self):
        return self._get_batch([], self.request.get('b_start', 0))

    def handle_sort_default(self):
        query = dict(portal_type='OpenMembership',
                     path=self.team_path,
                     review_state=self.active_states,
                     )
        mem_brains = self.catalog(**query)

        ids = [b.getId for b in mem_brains]
        query = dict(portal_type='OpenMember',
                     getId=ids,
                     sort_on='getId',
                     )
        results = self.membranetool(**query)
        return self._get_batch(results, self.request.get('b_start', 0))

    @memoizedproperty
    def memberships(self):
        try:
            sort_fn = getattr(self, 'handle_sort_%s' % self.sort_by)
            return sort_fn()
        except (TypeError, AttributeError):
            return self.handle_sort_default()
            
    def projects_for_member(self, member):
        # XXX these should be brains
        projects = self._projects_for_member(member)
        # only return max 10 results
        return projects[:10]

    def num_projects_for_member(self, member):
        projects = self._projects_for_member(member)
        return len(projects)

    @memoize_contextless
    def _projects_for_member(self, member):
        return member.getProjects()

    def membership_info_for(self, member):
        mem_id = member.getId()
        project = self.context
        project_id = project.getId()
        team = self.team
        membership = team._getOb(mem_id)

        contributions = 'XXX'
        activation = self.pretty_date(membership.made_active_date)
        modification = self.pretty_date(membership.ModificationDate())
        return dict(contributions=contributions,
                    activation=activation,
                    modification=modification,
                    )

    def is_admin(self, mem_id):
        return self.team.getHighestTeamRoleForMember(mem_id) == self.admin_role
        

class ManageTeamView(TeamRelatedView, formhandler.OctopoLite):
    """
    View class for the team management screens.
    """
    team_manage = ZopeTwoPageTemplateFile('team-manage.pt')
    team_manage_blank = ZopeTwoPageTemplateFile('team-manage-blank.pt')
    team_manage_macros = ZopeTwoPageTemplateFile('team-manage-macros.pt')

    mship_type = OpenMembership.portal_type

    # XXX REFACTOR: role_map is repeated in nui.member.view.MemberAccountView
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
        invites_util = getUtility(IEmailInvites)
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

    @property
    @req_memoize
    def email_sender(self):
        return EmailSender(self, mship_messages)

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
        return getUtility(ITransientMessage, context=self.portal)

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
            try:
                self.email_sender.sendEmail(mem_id, msg_id='request_approved',
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
                           }
            html = self.render_macro(self.team_manage_macros.macros['mshiprow'],
                                     extra_context=extra_context)
            res['mship-rows'] = {'action': 'append',
                                 'html': html,
                                 'effects':  'fadeIn'}

        plural = napproved != 1
        self.add_status_message(u'You have added %d member%s.' %
                                    (napproved, plural and 's' or ''))
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
        msg = u"Requests discarded: %s" % ', '.join(mem_ids)
        
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
        sender = self.email_sender
        msg = sender.constructMailMessage('request_denied',
                                          project_title=self.context.title)
        for mem_id in mem_ids:
            sender.sendEmail(mem_id, msg=msg)
            self._add_transient_msg_for(mem_id, 'You have been denied membership to')

        msg = u"Requests denied: %s" % ', '.join(mem_ids)
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
        sender = self.email_sender
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
            sender.sendEmail(mem_id, msg=msg)

        if deletes:
            self.team.manage_delObjects(ids=deletes)

        msg = u'Invitations removed: %s' % ', '.join(mem_ids)
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
        sender = self.email_sender
        for mem_id in mem_ids:
            acct_url = self._getAccountURLForMember(mem_id)
            # XXX if member hasn't logged in yet, acct_url will be whack
            #     probably okay b/c account creation auto-logs you in
            msg_vars = {'project_title': project_title,
                        'account_url': acct_url,
                        }
            sender.sendEmail(mem_id, msg_id='remind_invitee', **msg_vars)

        msg = "Reminders sent: %s" % ", ".join(mem_ids)
        self.add_status_message(msg)


    ##################
    #### EMAIL INVITATION BUTTON HANDLERS
    ##################

    @formhandler.action('remove-email-invites')
    def remove_email_invites(self, targets, fields=None):
        """
        Retracts invitations sent to email addresses.  Should send
        notifiers.
        """
        addresses = [urllib.unquote(t) for t in targets]

        sender = self.email_sender
        msg = sender.constructMailMessage('invitation_retracted',
                                          project_title=self.context.title)

        invite_util = getUtility(IEmailInvites)
        proj_id = self.context.getId()
        for address in addresses:
            invite_util.removeInvitation(address, proj_id)
            sender.sendEmail(address, msg=msg)

        msg = u'Email invitations removed: %s' % ', '.join(addresses)
        self.add_status_message(msg)

        ret = dict([(target, {'action': 'delete'}) for target in targets])
        return ret

    @formhandler.action('remind-email-invites')
    def remind_email_invites(self, targets, fields=None):
        """
        Sends an email reminder to the specified email invitees.
        """
        addresses = [urllib.unquote(t) for t in targets]
        sender = self.email_sender
        project_title = self.context.title
        for address in addresses:
            # XXX if member hasn't logged in yet, acct_url will be whack
            query_str = urllib.urlencode({'email': address})
            join_url = "%s/join?%s" % (self.portal.absolute_url(),
                                       query_str)
            msg_vars = {'project_title': project_title,
                        'join_url': join_url,
                        }
            sender.sendEmail(address, msg_id='invite_email', **msg_vars)

        msg = "Reminders sent: %s" % ", ".join(addresses)
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
        sender = self.email_sender
        ret = {}
        for mem_id in mems_removed:
            try:
                sender.sendEmail(mem_id, msg_id='membership_deactivated',
                                 project_title=self.context.title)
            except MailHostError:
                self.add_status_message('Error sending mail to: %s' % mem_id)
            self._add_transient_msg_for(mem_id, 'You have been deactivated from')
            ret[mem_id] = {'action': 'delete'}

        if mems_removed:
            msg = "Members deactivated: %s" % ', '.join(mems_removed)
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
                                   'team_manage_macros': self.team_manage_macros}
                    html = self.render_macro(self.team_manage_macros.macros['mshiprow'],
                                             extra_context=extra_context)
                    commands[mem_id] = {'action': 'replace',
                                        'html': html,
                                        'effects': 'highlight'}
                    transient_msg = (team.getHighestTeamRoleForMember(mem_id) == 'ProjectAdmin'
                                     and 'You are now an admin of'
                                     or 'You are no longer an admin of')
                    self._add_transient_msg_for(mem_id, transient_msg)
                        

            msg = u'Role changed for the following members: %s' \
                  % ', '.join(changes)
            self.add_status_message(msg)
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
        # XXX if member hasn't logged in yet, acct_url will be whack
        msg_subs = {'project_title': self.context.title,
                    'account_url': acct_url,
                    }
        self.email_sender.sendEmail(mem_id, msg_id='invite_member',
                                    **msg_subs)
        self.add_status_message(u'You invited %s to join this project.' % mem_id)


    ##################
    #### EMAIL INVITES BUTTON HANDLER
    ##################

    @formhandler.action('email-invites')
    def add_email_invites(self, targets=None, fields=None):
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
        invites = self.request.form.get('email-invites')
        invites = [addy.strip() for addy in invites.split(',')]
        regex = re.compile(EMAIL_RE)
        good = []
        bad = []
        for addy in invites:
            if addy: # ignore empty entries
                if regex.match(addy) is None:
                    bad.append(addy)
                else:
                    good.append(addy)
        if bad:
            psm = (u"Poorly formed email addresses, please correct: %s"
                   % ', '.join(bad))
            self.add_status_message(psm)
            return # don't do anything, just re-render the form

        utility = getUtility(IEmailInvites)
        proj_id = self.context.getId()
        proj_title = self.context.title
        mbtool = self.membranetool
        uSR = mbtool.unrestrictedSearchResults
        mem_invites = []
        mem_failures = []
        email_invites = []
        already_invited = []
        for addy in good:
            # first check to see if we're already a site member
            match = uSR(getEmail=addy)
            if match:
                # member already has this address
                brain = match[0]
                mem_id = brain.getId
                invited = self._doInviteMember(mem_id)
                if invited:
                    acct_url = self._getAccountURLForMember(mem_id)
                    msg_subs = {'project_title': proj_title,
                                'account_url': acct_url,
                                }
                    self.email_sender.sendEmail(mem_id,
                                                msg_id='invite_member',
                                                **msg_subs)
                    mem_invites.append(mem_id)
                else:
                    # invitation attempt failed
                    mem_failures.append(mem_id)
            else:
                # not a member
                if addy in utility.getInvitesByProject(proj_id):
                    already_invited.append(addy)
                else:
                    # perform invitation
                    utility.addInvitation(addy, proj_id)
                    query_str = urllib.urlencode({'email': addy})
                    join_url = "%s/join?%s" % (self.portal.absolute_url(),
                                               query_str)
                    msg_subs = {'project_title': self.context.title,
                                'join_url': join_url,
                                }
                    self.email_sender.sendEmail(addy, msg_id='invite_email',
                                                **msg_subs)
                    email_invites.append(addy)

        if mem_invites:
            self.add_status_message(u"Members invited: %s"
                                        % ', '.join(mem_invites))
        if mem_failures:
            self.add_status_message(u"Members for whom invitation failed: %s"
                                        % ', '.join(mem_failures))
        if already_invited:
            self.add_status_message(u"Emails already invited: %s"
                                        % ', '.join(already_invited))
        if email_invites:
            self.add_status_message(u"Email invitations: %s"
                                        % ', '.join(email_invites))

        self._norender = True
        self.redirect(self.request.ACTUAL_URL) # redirect clears form values
