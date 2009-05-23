from AccessControl import SecurityManagement
from AccessControl.User import UnrestrictedUser
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from Products.CMFCore.WorkflowCore import WorkflowException
from Products.CMFCore.utils import getToolByName
from opencore.browser.base import BaseView
from opencore.browser.formhandler import OctopoLite, action, post_only
from opencore.member.utils import member_path
from opencore.member.utils import get_cleanup_queue
from opencore.i18n import _
from opencore.interfaces.catalog import ILastWorkflowActor
from opencore.interfaces.event import JoinedProjectEvent
from opencore.interfaces.event import LeftProjectEvent
from opencore.interfaces.event import MemberModifiedEvent
from opencore.interfaces.message import ITransientMessage
from plone.memoize.view import memoize as req_memoize
from zope.component import getAdapter
from zope.event import notify
import logging


logger = logging.getLogger('opencore.member.browser.account')

class MemberAccountView(BaseView, OctopoLite):

    template = ZopeTwoPageTemplateFile('account.pt')
    project_table = ZopeTwoPageTemplateFile('account_project_table.pt')
    project_row = ZopeTwoPageTemplateFile('account_project_row.pt')

    active_states = ['public', 'private']
    msg_category = 'membership'

    @property
    @req_memoize
    def _mship_brains(self, **extra):
        user_id = self.viewed_member_info['id']
        query = dict(portal_type='OpenMembership',
                     getId=user_id,
                     )
        query.update(extra)
        mship_brains = self.catalog(**query)
        return mship_brains

    def _project_metadata_for(self, project_id):
        portal = self.portal
        portal_path = '/'.join(portal.getPhysicalPath())
        projects_folder = 'projects'
        path = [portal_path, projects_folder, project_id]
        path = '/'.join(path)
        project_info = self.catalog.getMetadataForUID(path)
        return project_info

    def _project_id_from(self, brain):
        path = brain.getPath()
        elts = path.split('/')
        project_id = elts[-2]
        return project_id

    @req_memoize
    def _create_project_dict(self, brain):
        project_id = self._project_id_from(brain)
        project_info = self._project_metadata_for(project_id)
        proj_title = project_info['Title']
        proj_id = project_info['getId']
        proj_policy = project_info['project_policy']
        project = self.portal.projects[proj_id]

        review_state = brain.review_state
        is_pending = review_state == 'pending'

        # note that pending members will not be listed in the template
        listed = review_state == 'public'

        since = None
        if is_pending:
            since = brain.lastWorkflowTransitionDate
        else:
            since = brain.made_active_date
        since = self.pretty_date(since)

        role = brain.highestTeamRole

        return dict(title=proj_title,
                    proj_id=proj_id,
                    since=since,
                    listed=listed,
                    role=role,
                    is_pending=is_pending,
                    proj_policy=proj_policy,
                    description=project.Description(),
                    logo=project.getLogo(),
                    )


    def _projects_satisfying(self, pred):
        brains = filter(pred, self._mship_brains)
        return map(self._create_project_dict, brains)

    @property
    @req_memoize
    def projects_for_user(self):
        """this should include all active mships as well as member requests"""
        def is_user_project(brain):
            if brain.review_state == 'pending':
                return brain.lastWorkflowActor == self.viewed_member_info['id']
            return brain.review_state in self.active_states
        return sorted(self._projects_satisfying(is_user_project), key=lambda x:x['title'].lower())

    @req_memoize
    def invitations(self):
        """ return mship brains for pending project invitations """
        def is_invitation(brain):
            return brain.review_state == 'pending' and \
                   brain.lastWorkflowActor != self.viewed_member_info['id']
        return self._projects_satisfying(is_invitation)

    @property
    @req_memoize
    def member_requests(self):
        """ return all proj_ids for pending member requests """
        def is_member_request(brain):
            return brain.review_state == 'pending' and \
                   brain.lastWorkflowActor == self.viewed_member_info['id']
        return self._projects_satisfying(is_member_request)

    @req_memoize
    def _membership_for_proj(self, proj_id):
        team = self.get_tool('portal_teams').getTeamById(proj_id)
        mem_id = self.viewed_member_info['id']
        mship = team._getMembershipByMemberId(mem_id)
        return mship

    def _apply_transition_to(self, proj_id, transition):
        ### XXX this apply_transition_to function strikes me as highly questionable.
        # maybe it belongs in opencore.content somewhere? note that it's kind of
        # identical to opencore.project.browser.view.doMshipWFAction...
        mship = self._membership_for_proj(proj_id)
        try:
            mship.do_transition(transition)
            return True
        except WorkflowException:
            return False

    def leave_project(self, proj_id):
        """ remove membership by marking the membership object as inactive """
        if not self._can_leave(proj_id): return False

        if self._is_only_admin(proj_id):
            proj = self.portal.projects[proj_id]
            proj_title = unicode(proj.Title(), 'utf-8') # accessor always will return ascii

            only_admin_msg = _(u'psm_leave_project_admin',
                               u'You are the only administrator of "${proj_title}". You can\'t leave this ${project_noun} without appointing another.',
                               mapping={u'proj_title':proj_title,
                                        u'project_noun':self.project_noun})
            
            self.addPortalStatusMessage(only_admin_msg)
            return False

        if self._apply_transition_to(proj_id, 'deactivate'):
            mship = self._membership_for_proj(proj_id)
            notify(LeftProjectEvent(mship))
            return True
        else:
            msg = _(u'psm_cannot_leave_project',
                    u'You cannot leave this ${project_noun}.',
                    mapping={u'project_noun': self.project_noun})
            self.addPortalStatusMessage(msg)
            return False

    def change_visibility(self, proj_id, to=None):
        """
        change whether project members appear in listings
        
        if to is None: toggles project member visibility
        if to is one of 'public', 'private': set visibility to that

        return True iff visibility changed
        """
        mship = self._membership_for_proj(proj_id)
        wft = self.get_tool('portal_workflow')
        cur_state = wft.getInfoFor(mship, 'review_state')
        if to == None:
            if cur_state == 'public':
                wft.doActionFor(mship, 'make_private')
            else:
                wft.doActionFor(mship, 'make_public')
            return True
        elif to == cur_state or to not in ('public', 'private'):
            return False
        else:
            wft.doActionFor(mship, 'make_%s' % to)
            return True

    def _get_projinfo_for_id(self, proj_id):
        """ optimize later """
        def is_user_project(brain):
            if brain.review_state == 'pending':
                return brain.lastWorkflowActor == self.viewed_member_info['id']
            return brain.review_state in self.active_states

        user_id = self.viewed_member_info['id']
        query = dict(portal_type='OpenMembership',
                     getId=user_id,
                     )
        mship_brains = self.catalog(**query)
        mship_brains = map(self._create_project_dict,
                           filter(is_user_project, mship_brains))
        mship_brains = [i for i in mship_brains if i['proj_id'] == proj_id]
        return mship_brains[0]

    @action('change-listing')
    def change_visilibity_handler(self, targets, fields=None):
        ret = {}
        for proj_id, field in zip(targets, fields):
            new_visibility = field['listing']
            if self.change_visibility(proj_id, new_visibility):
                projinfo = self._get_projinfo_for_id(proj_id)
                
                ret['mship_%s' % proj_id] = {
                    'html': self.project_row(proj_id=proj_id,
                                             projinfo=projinfo),
                    'action': 'replace',
                    'effects': 'highlight'}
        return ret

    def _can_leave(self, proj_id):
        mship = self._membership_for_proj(proj_id)
        last_actor = ILastWorkflowActor(mship).getValue()
        wft = self.get_tool('portal_workflow')
        mem_id = self.viewed_member_info['id']

        review_state = wft.getInfoFor(mship, 'review_state')

        is_active = review_state in self.active_states
        is_pending_member_requested = review_state == 'pending' and \
                                      last_actor == mem_id

        return is_active or is_pending_member_requested

    def _is_only_admin(self, proj_id, mem_id=None):
        team = self.get_tool('portal_teams').getTeamById(proj_id)

        # for some reason checking the role is not enough
        # I've gotten ProjectAdmin roles back for a member
        # in the pending state
        if mem_id is None:
            mem_id = self.viewed_member_info['id']

        mship = team._getOb(mem_id)
        wft = self.get_tool('portal_workflow')
        review_state = wft.getInfoFor(mship, 'review_state')
        if review_state not in self.active_states: return False

        role = team.getHighestTeamRoleForMember(mem_id)
        if role != 'ProjectAdmin': return False

        project_admins = team.get_admin_ids()

        return len(project_admins) <= 1

    @action('leave')
    def leave_handler(self, targets, fields=None):
        json_ret = {}
        for proj_id in targets:
            if self.leave_project(proj_id):
                elt_id = 'mship_%s' % proj_id
                json_ret[elt_id] = dict(action='delete')
        json_ret['num_projs'] = {'html': len(self.projects_for_user),
                                 'action': 'copy'}
        return json_ret

    @action('AcceptInvitation')
    def accept_handler(self, targets, fields=None):
        assert len(targets) == 1
        proj_id = targets[0]

        if not self._apply_transition_to(proj_id, 'approve_public'):
            return {}

        # security reindex (async to the catalog queue)
        team = self.get_tool('portal_teams').getTeamById(proj_id)
        team.reindexTeamSpaceSecurity()

        admin_ids = team.get_admin_ids()
        transient_msgs = ITransientMessage(self.portal)
        id_ = self.loggedinmember.getId()
        member_url = u'%s/%s' % (getToolByName(self.context, 'portal_url')(),
                                 member_path(id_))
        project_url = self.project_url(proj_id)
        msg = _(u'tmsg_joined_project',
                u'<a href="${member_url}">${id}</a> has joined <a href="${project_url}">${proj_id}</a>',
                mapping={u'id':id_, u'project_url':project_url, u'proj_id':proj_id, u'member_url':member_url})
        for mem_id in admin_ids:
            transient_msgs.store(mem_id, "membership", msg)
        
        projinfos = self.projects_for_user
        if len(projinfos) > 1:
            projinfo = self._get_projinfo_for_id(proj_id)
            new_proj_row = self.project_row(proj_id=proj_id, projinfo=projinfo)
            command = {'projinfos_for_user': {'action': 'append',
                                              'effects': 'highlight',
                                              'html': new_proj_row
                                              }}
        else:
            new_proj_table = self.project_table()
            command = {'project_table': {'action': 'replace',
                                         'html': new_proj_table
                                         }}

        elt_id = '%s_invitation' % proj_id
        
        command.update(ajax_update(elt_id, self.nupdates()))

        mship = team._getOb(id_)
        notify(JoinedProjectEvent(mship))

        return command

    @action('DenyInvitation')
    def deny_handler(self, targets, fields=None):
        assert len(targets) == 1
        proj_id = targets[0]

        if not self._apply_transition_to(proj_id, 'reject_by_owner'):
            return {}

        id_ = self.loggedinmember.getId()

        # there must be a better way to get the last wf transition which was an invite... right?
        wftool = self.get_tool("portal_workflow")
        team = self.get_tool("portal_teams").getTeamById(proj_id)
        mship = team.getMembershipByMemberId(id_)
        wf_id = wftool.getChainFor(mship)[0]
        wf_history = mship.workflow_history.get(wf_id)
        spurned_admin = [i for i in wf_history if i['review_state'] == 'pending'][-1]['actor']
        
        transient_msgs = ITransientMessage(self.portal)

        member_url = u'%s/%s' % (getToolByName(self.context, 'portal_url')(),
                                 member_path(id_))
        project_url = self.project_url(proj_id)
        msg = _(u'tmsg_decline_invite',
                u'<a href="${member_url}">${id}</a> has declined your invitation to join <a href="${project_url}">${proj_id}</a>',
                mapping={u'id':id_, u'project_url':project_url, u'proj_id':proj_id, u'member_url':member_url})
        transient_msgs.store(spurned_admin, "membership", msg)

        elt_id = '%s_invitation' % proj_id
        return ajax_update(elt_id, self.nupdates())

    # XXX is there any difference between ignore and deny?
    ## currently unused
    @action('IgnoreInvitation')
    def ignore_handler(self, targets, fields=None):
        assert len(targets) == 1
        proj_id = targets[0]
        # XXX do we notify anybody (proj admins) when a mship has been denied?
        if not self._apply_transition_to(proj_id, 'reject_by_owner'):
            return {}
        elt_id = '%s_invitation' % proj_id
        return ajax_update(elt_id, self.nupdates())

    @action('close')
    def close_msg_handler(self, targets, fields=None):
        assert len(targets) == 1
        idx = targets[0]
        idx = int(idx)
        # XXX explicit context shouldn't be req'd, but lookup fails
        # in the tests w/o it  :(
        tm = ITransientMessage(self.portal)
        mem_id = self.viewed_member_info['id']
        try:
            tm.pop(mem_id, self.msg_category, idx)
        except KeyError:
            return {}
        else:
            elt_id = 'close_info_message_%s' % idx
            return ajax_update(elt_id, self.nupdates())

    @property
    @req_memoize
    def infomsgs(self):
        """info messages re project admission/rejection
        
           tuples are returned in the form of (idx, msg)
           so that they can be popped by the user"""
        # XXX explicit context shouldn't be req'd, but lookup fails
        # in the tests w/o it  :(
        tm = ITransientMessage(self.portal)
        mem_id = self.viewed_member_info['id']
        msgs = tm.get_msgs(mem_id, self.msg_category)
        return msgs

    @action("change-password")
    def change_password(self, target=None, fields=None):
        """allows members to change their password"""
        passwd_curr = self.request.form.get('passwd_curr')
        password = self.request.form.get('password')
        password2 = self.request.form.get('password2')

        self.request.form['confirm_password'] = password2

        member = self.viewedmember()
        mem_id = self.viewed_member_info['id']

        if not member.verifyCredentials({'login': mem_id,
                                        'password': passwd_curr}):
            self.addPortalStatusMessage(_(u'psm_check_old_password', u'Please check the old password you entered.'))
            return

        if self.validate_password_form(password, password2, member):

            member._setPassword(password)
            self.addPortalStatusMessage(_(u'psm_password_changed', u'Your password has been changed.'))

    def nupdates(self):
        return len(self.infomsgs) + len(self.invitations())

    @property
    def invitation_actions(self):
        return ['Accept', 'Deny']

    @action("change-email")
    def change_email(self, target=None, fields=None):
        """allows members to change their email address"""
        email = self.request.form.get('email')
        hide_email = bool(self.request.form.get('hide_email'))

        if not email:
            self.addPortalStatusMessage(_(u'psm_enter_new_email',
                                          u'Please enter your new email address.'))
            return

        mem = self.loggedinmember
        msg = mem.validate_email(email)
        if msg:
            self.addPortalStatusMessage(msg)
            return

        if mem.getEmail() == email:
            return

        mem.setEmail(email)
        mem.reindexObject(idxs=['getEmail'])
        notify(MemberModifiedEvent(mem))
        self.addPortalStatusMessage(_(u'psm_email_changed', u'Your email address has been changed.'))

    def pretty_role(self, role):
        role_map = dict(ProjectAdmin='administrator',
                        ProjectMember='member')
        role = role_map.get(role, role)
        return role

class ProjectInvitationsView(MemberAccountView):
    """
    view of the members project invitations
    XXX: could be generalized
    XXX: should go to the general pattern of `content -> adapter -> view`
    looks to me like this could be a viewlet? --egj
    """

    template = ZopeTwoPageTemplateFile('invitations.pt') # could change this

class TourView(MemberAccountView):
    """ dummy view for the 1page tour 
    
    XXX: this shouldn't need to inherit from memberaccountview;
         should find the necessary functions and turn them into
         content adapters or viewlets. -egj
    """

    template = ZopeTwoPageTemplateFile('tour.pt')

    def has_projects(self):
        if self.invitations() or self.projects_for_user:
            return True
        return False

class ProjectInvitationsView(MemberAccountView):
    """
    view of the members project invitations
    XXX: could be generalized
    XXX: should go to the general pattern of `content -> adapter -> view`
    """

    template = ZopeTwoPageTemplateFile('invitations.pt') # could change this


def ajax_update(elt_id, nupdates):
    """helper function to generate the ajax required to update the
       account page"""
    if nupdates <= 0:
        num_updates_top = ''
    else:
        num_updates_top = '(%s)' % nupdates

    return {elt_id: dict(action='delete'),
            'num_updates': dict(action='copy',
                                html=nupdates),
            'num_updates_menu': dict(action='copy',
                                     html=nupdates),
            'num_updates_top': dict(action='copy',
                                    html=num_updates_top)}


class DeleteAccountView(BaseView):
    """
    Delete the currently viewed account.
    """

    def handle_request(self):
        delete = self.request.form.get('delete')
        if delete:
            return self.handle_delete()
        elif delete == 0:
            return self.handle_cancel()

    def handle_cancel(self):
        self.addPortalStatusMessage(_(u'psm_account_not_deleted',
                                      u'Account not deleted.'))
        return self.redirect(self.context.absolute_url() + '/account')

    @post_only(raise_=True)
    def handle_delete(self):
        mship = getToolByName(self.context, 'portal_membership')
        user_to_delete = self.viewed_member_info['id']
        old_manager = SecurityManagement.getSecurityManager()
        current_user = old_manager.getUser().getId()
        # To avoid blocking while we traverse the entire contents of the site,
        # we quickly delete the member and their own content...
        if current_user == user_to_delete:
            # Normally, users don't have permission to delete users.
            # Make an exception for deleting yourself.
            superuser = UnrestrictedUser('superuser', '', [], [])
            SecurityManagement.newSecurityManager(self.request, superuser)
            mship.deleteMembers([user_to_delete], delete_memberareas=True,
                                delete_localroles=False)
            SecurityManagement.setSecurityManager(old_manager)
            self.context.acl_users.logout(self.request)
        else:
            # Otherwise, rely on normal access controls.  This will
            # allow site admins (and only site admins) to delete
            # anybody.
            mship.deleteMembers([user_to_delete], delete_memberareas=True,
                                delete_localroles=False)
        portal_url = getToolByName(self.context, 'portal_url')()
        self.addPortalStatusMessage(
            _(u'psm_account_deleted',
              u'Account ${deleted_user_id} has been permanently deleted.',
              mapping={u'deleted_user_id': user_to_delete})
        return self.redirect(portal_url)

        
class AccountCleanupQueueView(object):

    """Handle a queue of account post-deletion cleanup jobs, each of
    which may take a long time.  So this is intended to be run
    asynchronously, eg. by clockserver.

    (which, incidentally, is why this is a view... clockserver needs
    something it can visit by URL)
    """

    def __init__(self, context, request):
        self.context = context  # Should be the portal.
        self.request = request
        self.queue = get_cleanup_queue(self.context)
        self.mship_tool = getToolByName(self.context, 'portal_membership')

    def __call__(self):
        members = set()
        if self.queue:
            deletion_time = self.queue[0]['deleted'].strftime('%Y-%m-%d %H:%M:%S')
            while self.queue:
                # A queue is kind of silly here, since we try to
                # consume the whole thing. But it works, and I figured
                # I'd use the same infrastructure for other
                # long-running tasks like project export.
                info = self.queue.pull()
                members.add(info['id'])
        if members:
            # This does not handle failure at all!!!
            #
            # Most likely failure would be a ConflictError eg. if you
            # double-submit the delete form, which should hopefully
            # succeed when automatically retried.
            #
            # Worse, there's a race condition if you delete a member
            # and then re-add a member of the same id before this view
            # runs; in that case the new user will be created but then
            # be stripped of any local roles they're supposed to have.
            # You can see such problems if you eg. run the remove_user
            # flunc suite in a loop. Or you might just get unlucky
            # during any flunc run.
            #
            # That's all a pain, but I judge this to be less dangerous
            # than the potential security hole of not cleaning up
            # local roles. - PW
            members = sorted(members)
            logger.debug('Cleaning local roles for deleted users: %r' % members)
            self.mship_tool.deleteLocalRoles(self.context, members,
                                             reindex=True, recursive=True)
            logger.info('Cleaned up local roles for members: %r'
                        ' (first was deleted at %s)' % (members, deletion_time))
        logger.debug('cleanup done')
