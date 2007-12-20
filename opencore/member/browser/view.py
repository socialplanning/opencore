from App import config
from DateTime import DateTime
from Products.AdvancedQuery import Eq
from Products.CMFCore.WorkflowCore import WorkflowException
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import transaction_note
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from datetime import datetime
from datetime import timedelta
from opencore.interfaces.catalog import ILastWorkflowActor
from opencore.interfaces.event import JoinedProjectEvent
from opencore.interfaces.event import LeftProjectEvent
from opencore.interfaces.event import MemberEmailChangedEvent
from opencore.interfaces.membership import IEmailInvites
from opencore.browser.base import BaseView, _
from opencore.browser.formhandler import OctopoLite, action
from opencore.interfaces.message import ITransientMessage
from opencore.project.utils import project_path
from plone.memoize.view import memoize as req_memoize
from time import gmtime
from time import strftime
from topp.utils.pretty_date import prettyDate
from urlparse import urlsplit
from urlparse import urlunsplit
from zope.app.event.objectevent import ObjectModifiedEvent
from zope.component import getUtility
from zope.event import notify


class ProfileView(BaseView):

    field_snippet = ZopeTwoPageTemplateFile('field_snippet.pt')
    member_macros = ZopeTwoPageTemplateFile('member_macros.pt') 

    # XXX this seems to be called twice when i hit /user/profile 
    #     or /user/profile/edit ... why is that?
    def __init__(self, context, request):
        BaseView.__init__(self, context, request)
        self.public_projects = []
        self.private_projects = []

    def populate_project_lists(self):
        mship_proj_map = self.mship_proj_map()
        for (_, m) in mship_proj_map.items():
            mship = m['mship']
            proj = m['proj']
            if mship.review_state == 'private' or proj.review_state == 'closed':
                self.private_projects.append(proj)
            else:
                self.public_projects.append(proj)

            sortfunc = lambda x: x.Title.lower()
            self.private_projects.sort(key=sortfunc)
            self.public_projects.sort(key=sortfunc)


    def activity(self, max=10):
        """Returns a list of dicts describing each of the `max` most recently
        modified wiki pages for the viewed user."""
        memberid = self.viewed_member_info['id']
        query = Eq('Creator', memberid) | Eq('lastModifiedAuthor', memberid)
        query &= Eq('portal_type', 'Document') #| Eq('portal_type', 'OpenProject')
        brains = self.catalog.evalAdvancedQuery(query, (('modified', 'desc'),)) # sort by most recent first ('desc' means descending)
        brains = brains[:max] # there appears to be no way to specify the max in the query

        def dictify(brain):
            d = dict(title = brain.Title,
                     url   = brain.getURL(),
                     date  = prettyDate(DateTime(brain.ModificationDate)))

            try:
                path = brain.getPath().split('/')
                # get index of the projects folder
                pfindex = path.index('projects') # TODO don't hard code projects folder
                projid = path[pfindex + 1]
                projpath = '/'.join(path[:pfindex+2])
                projmeta = self.catalog.getMetadataForUID(projpath)
                d['project'] = projmeta['Title']

                # get index of the right-most '/'
                rslashindex = d['url'].rindex('/')
                d['projurl'] = d['url'][:rslashindex]

            except ValueError:
                # this page brain must not be inside a project
                d.update(project=None, projurl=None)

            return d

        return [dictify(brain) for brain in brains]

    def viewingself(self):
        return self.viewedmember() == self.loggedinmember

    def mangled_portrait_url(self):
        """When a member changes her portrait, her portrait_url remains the same.
        This method appends a timestamp to portrait_url to trick the browser into
        fetching the new image instead of using the cached one which could be --
        and always will be in the ajaxy-change-portrait case -- out of date.
        P.S. This is an ugly hack."""
        portrait_url = self.viewed_member_info.get('portrait_url')
        if portrait_url == self.defaultPortraitURL:
            return portrait_url
        timestamp = str(DateTime()).replace(' ', '_')
        return '%s?%s' % (portrait_url, timestamp)

    def trackbacks(self):
        self.msg_category = 'Trackback'

        tm = ITransientMessage(self.portal)
        mem_id = self.viewed_member_info['id']
        msgs = tm.get_msgs(mem_id, self.msg_category)

        timediff = datetime.now() - timedelta(days=60)
        old_messages = [(idx, value) for (idx, value) in msgs if value['time'] < timediff]
        for (idx, value) in old_messages:
            tm.pop(mem_id, self.msg_category, idx)
        if not old_messages:
            msgs = tm.get_msgs(mem_id, self.msg_category)

        # We want to insert the indexes into the values so that we can properly address them for deletion
        addressable_msgs = []
        for (idx, value) in msgs:
            if 'excerpt' not in value.keys():
                tm.pop(mem_id, self.msg_category, idx)
                value['excerpt'] = ''
                tm.store(mem_id, self.msg_category, value)

                # XXX TODO: We don't want to display escaped HTML entities,
                # eg. if the comment text contains "I paid &#8364;20
                # for mine" we want the user to see the euro symbol,
                # not the entity code.  But we don't want to just
                # throw them away either.  We could leave the data
                # alone and use "structure" in the template; but then
                # we're assuming the data is safe, and it's only as
                # trustworthy as the openplans user.  Below is some
                # code that just throws the entities (and all HTML)
                # away.  Maybe we could convert entities to unicode
                # prior to or instead of calling detag?  Can do that
                # using Beautiful Soup, see: http://tinyurl.com/28ugnq

#             from topp.utils.detag import detag
#             for k, v in value.items():
#                 if isinstance(v, basestring):
#                     value[k] = detag(v)
            value['idx'] = 'trackback_%d' % idx
            value['close_url'] = 'trackback-delete?idx=%d' % idx
            value['pub_date']    = prettyDate(value['time'])
            addressable_msgs.append(value)

        return addressable_msgs

    @property
    def geo_info(self):
        """geo information for display in forms;
        takes values from request, falls back to existing member info
        if possible."""
        info = self._get_geo_info(self.member_info)
        geo = self.context.restrictedTraverse('oc-geo-read')
        # Override the static map image size. Ugh, sucks to have this in code.
        info['static_img_url'] = geo.location_img_url(width=285, height=285)
        return info

class ProfileEditView(ProfileView, OctopoLite):

    portrait_snippet = ZopeTwoPageTemplateFile('portrait-snippet.pt')
    template = ZopeTwoPageTemplateFile('profile-edit.pt')

    def has_invitations(self):
        """check whether the member has any pending project
        invitations to manage"""
        member = self.loggedinmember
        cat = self.catalogtool
        pending_mships = cat(portal_type='OpenMembership',
                             review_state='pending')
        return bool(pending_mships)

    def check_portrait(self, member, portrait):
        try:
            member.setPortrait(portrait)
        except ValueError: # must have tried to upload an unsupported filetype
            self.addPortalStatusMessage(_(u'psm_choose_image', u'Please choose an image in gif, jpeg, png, or bmp format.'))
            return False
        return True

    @action("uploadAndUpdate")
    def change_portrait(self, target=None, fields=None):
        member = self.viewedmember()
        portrait = self.request.form.get("portrait")

        if not self.check_portrait(member, portrait):
            return

        member.reindexObject('portrait')
        return {
            'oc-profile-avatar' : {
                'html': self.portrait_snippet(),
                'action': 'replace',
                'effects': 'highlight'
                }
            }

    @action("remove")
    def remove_portrait(self, target=None, fields=None):
        member = self.viewedmember()
        member.setPortrait("DELETE_IMAGE")  # AT API nonsense
        member.reindexObject('portrait')
        return {
            'oc-profile-avatar' : {
                'html': self.portrait_snippet(),
                'action': 'replace',
                'effects': 'highlight'
                }
            }

    @action("update")
    def handle_form(self, target=None, fields=None):
        member = self.viewedmember()

        # deal with portrait first
        portrait = self.request.form.get('portrait')
        if portrait:
            if not self.check_portrait(member, portrait):
                return
            del self.request.form['portrait']

        # handle geo stuff
        coords = self.geocode_from_form()
        locationchanged = False
        form = self.request.form
        if self.set_geolocation(coords):
            locationchanged = True
        elif member.getLocation() != form.get('location', ''):
            locationchanged = True
        if form.get('position-text'):
            member.setPositionText(form['position-text'])
        for key in ('position-latitude', 'position-longitude', 'position-text'):
            if form.has_key(key):
                del form[key]

        # now deal with the rest of the fields
        for field, value in form.items():
            mutator = 'set%s' % field.capitalize()
            mutator = getattr(member, mutator, None)
            if mutator is not None:
                mutator(value)
            self.user_updated()

        notify(ObjectModifiedEvent(member))
    
        member.reindexObject()
        self.template = None
        return self.redirect('profile')
        
    def user_updated(self): # TODO
        """callback to tell taggerstore a user updated (possibly) taggifiable
        fields. something like a POST to /taggerstore/."""
        pass


class MemberAccountView(BaseView, OctopoLite):

    template = ZopeTwoPageTemplateFile('account.pt')
    project_table = ZopeTwoPageTemplateFile('account_project_table.pt')
    project_row = ZopeTwoPageTemplateFile('account_project_row.pt')

    active_states = ['public', 'private']
    msg_category = 'membership'

    # DWM: application specific term should be part of method names
    # probably indicate this needs to be behind an api
    def twirlip_uri(self):
        cfg = config.getConfiguration().product_config.get('opencore.nui')
        if cfg:
            return cfg.get('twirlip_uri', '')
        else:
            #this will fail, but at least looking at the source, we'll know why.
            return 'http://twirlip.example.com'

    @property
    @req_memoize
    def _mship_brains(self, **extra):
        user_id = self.viewed_member_info['id']
        query = dict(portal_type='OpenMembership',
                     getId=user_id,
                     )
        query.update(extra)
        mship_brains = self.catalogtool(**query)
        return mship_brains

    def _project_metadata_for(self, project_id):
        portal = self.portal
        portal_path = '/'.join(portal.getPhysicalPath())
        projects_folder = 'projects'
        path = [portal_path, projects_folder, project_id]
        path = '/'.join(path)

        cat = self.catalogtool
        project_info = cat.getMetadataForUID(path)
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

            only_admin_msg = _(u'psm_leave_project_admin', u'You are the only remaining administrator of "${proj_title}". You can\'t leave this project without appointing another.',
                               mapping={u'proj_title':proj_title})
            
            self.addPortalStatusMessage(only_admin_msg)
            return False

        if self._apply_transition_to(proj_id, 'deactivate'):
            mship = self._membership_for_proj(proj_id)
            notify(LeftProjectEvent(mship))
            return True
        else:
            self.addPortalStatusMessage(_(u'psm_cannot_leave_project', u'You cannot leave this project.'))
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
        mship_brains = self.catalogtool(**query)
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
        project_url = '/'.join((self.url_for('projects'), proj_id))
        msg = _(u'tmsg_joined_project', u'${id} has joined <a href="${project_url}">${proj_id}</a>',
                mapping={u'id':id_, u'project_url':project_url, u'proj_id':proj_id})
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
        
        command.update({
                elt_id: {'action':'delete'},
                "num_updates": {'action': 'copy',
                                'html': self.nupdates()}
                })

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

        project_url = '/'.join((self.url_for('projects'), proj_id))
        msg = _(u'tmsg_decline_invite', u'${id} has declined your invitation to join <a href="${project_url}">${proj_id}</a>',
                mapping={u'id':id_, u'project_url':project_url, u'proj_id':proj_id})
        transient_msgs.store(spurned_admin, "membership", msg)

        elt_id = '%s_invitation' % proj_id
        return {elt_id: dict(action='delete'),
                "num_updates": {'action': 'copy',
                                'html': self.nupdates()}}

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
        return {elt_id: dict(action='delete'),
                "num_updates": {'action': 'copy',
                                'html': self.nupdates()}}

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
            elt_id = '%s_close' % idx
            return {elt_id: dict(action='delete'),
                    "num_updates": {'action': 'copy',
                                    'html': self.nupdates()}}

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
            self.addPortalStatusMessage(_(u'psm_enter_new_email', u'Please enter your new email address.'))
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
        notify(MemberEmailChangedEvent(mem))
        self.addPortalStatusMessage(_(u'psm_email_changed', u'Your email address has been changed.'))

    def pretty_role(self, role):
        role_map = dict(ProjectAdmin='administrator',
                        ProjectMember='member')
        role = role_map.get(role, role)
        return role


class TrackbackView(BaseView):
    """handle trackbacks"""

    msg_category = 'Trackback'

    def __call__(self):
        # Add a trackback and return a javascript callback
        # so client script knows when it's done and whether it succeeded.
        mem_id = self.viewed_member_info['id']
        tm = ITransientMessage(self.portal)

        if self.viewedmember() != self.loggedinmember:
            return 'OpenCore.submitstatus(false, "Permission denied");'

        # check for all variables
        url = self.request.form.get('commenturl')
        title = self.request.form.get('title')
        blog_name = self.request.form.get('blog_name', 'an unnamed blog')
        comment = self.request.form.get('comment')
        if None in (url, comment):
            msg = (url == None) and "url not provided" or "comment not provided"
            return 'OpenCore.submitstatus(false, "%s")' % msg
        if not title:
            excerpt = comment.split('.')[0]
            title = excerpt[:100]
            if title != excerpt:
                title += '...'

        tm.store(mem_id, self.msg_category, {'url':url, 'title':title, 'blog_name':blog_name, 'excerpt':comment, 'time':datetime.now()})
        return 'OpenCore.submitstatus(true);'


    def delete(self):
        mem_id = self.viewed_member_info['id']

        if urlsplit(self.request['HTTP_REFERER'])[1] != urlsplit(self.siteURL)[1]:
            self.request.response.setStatus(403)
            return 'Cross site deletes not allowed!'

        # XXX todo 
        #     a) move this to @nui.formhandler.post_only 
        #     b) use that
        if self.request['REQUEST_METHOD'] != 'POST':
            self.request.response.setStatus(405)
            return 'Not Post'
        if self.viewedmember() != self.loggedinmember:
            self.request.response.setStatus(403)
            return 'You must be logged in to modify your posts!'

        index = self.request.form.get('idx')
        if index is None:
            self.request.response.setStatus(400)
            return 'No index specified'

        # Do the delete
        tm = ITransientMessage(self.portal)
        tm.pop(mem_id, self.msg_category, int(index))
        # TODO: Make sure this is an AJAX request before sending an AJAX response
        #       by using octopus/octopolite
        return {'trackback_%s' % index: {'action': 'delete'}}


class TourView(MemberAccountView):
    """ dummy view for the 1page tour """

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


