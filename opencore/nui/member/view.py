from datetime import datetime

from zope import event
from zope.app.annotation.interfaces import IAnnotations

from zExceptions import BadRequest
from zExceptions import Redirect
from Missing import MV

from plone.memoize.view import memoize as req_memoize

from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import transaction_note
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile

from topp.utils.pretty_date import prettyDate

from opencore.nui.base import BaseView, button
from opencore.nui.formhandler import OctopoLite, action
        
class ProfileView(BaseView):

    field_snippet = ZopeTwoPageTemplateFile('field_snippet.pt')

    def activity(self, max=5):
        """Returns a list of dicts describing each of the `max` most recently
        modified wiki pages for the viewed user."""
        query = dict(Creator=self.viewedmember().getId(),
                     portal_type='Document',
                     sort_on='modified',
                     sort_order='reverse',
                     limit=max)
        brains = self.catalog.searchResults(**query)

        def dictify(brain):
            return {'title': brain.Title,
                    'url':   brain.getURL(),
                    'date':  prettyDate(brain.getRawCreation_date())}

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
        timestamp = datetime.now().isoformat()
        return '%s?%s' % (portrait_url, timestamp)


class ProfileEditView(ProfileView):

    portrait_snippet = ZopeTwoPageTemplateFile('portrait-snippet.pt')

    def handle_form(self):
        """ quick 'n' dirty for now. """ 
        member = self.viewedmember()
        portrait = self.request.form.get('portrait')
        mode = self.request.form.get('mode')
        task = self.request.form.get('task', '')
      
        # TODO resize portrait if necessary

        print "task is %s" % task
        if 'uploadAndUpdate' in task:
            if portrait:
                member.setPortrait(portrait)
                member.reindexObject()
 
            #don't do this yet!!!
	    #return {
            #       'oc-profile-avatar' : 
            #         {
            #         'html': self.portrait_snippet(),
            #         'action': 'replace',
            #         'effects': 'highlight'
            #         }
            #       }
        elif 'remove' in task:
            member.setPortrait(None)  ## XXX TODO ASAP fix this line to be correct
            member.reindexObject()
            #don't do this yet!!!
	    #return {
            #       'oc-profile-avatar' : 
            #         {
            #         'html': self.portrait_snippet(),
            #         'action': 'replace',
            #         'effects': 'highlight'
            #         }
            #       }

        else:
            for field, value in self.request.form.items():
                mutator = 'set%s' % field.capitalize()
                mutator = getattr(member, mutator, None)
                if mutator is not None:
                    mutator(value)
                self.user_updated()
    
            member.reindexObject()
        return self.redirect('profile')


    def user_updated(self): # TODO
        """callback to tell taggerstore a user updated (possibly) taggifiable
        fields. something like a POST to /taggerstore/."""
        pass


class MemberPreferences(BaseView, OctopoLite):

    template = ZopeTwoPageTemplateFile('preferences.pt')

    active_states = ['public', 'private']

    @property
    @req_memoize
    def _mship_brains(self):
        user_id = self.context.getId()
        query = dict(portal_type='OpenMembership',
                     getId=user_id,
                     )
        mship_brains = self.catalogtool(**query)
        return mship_brains

    def _project_metadata_for(self, project_id):
        portal = self.portal
        portal_path = portal.absolute_url_path()
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

        made_active_date = brain.made_active_date
        if made_active_date == MV:
            mship_activated_on = 'unknown'
        else:
            mship_activated_on = self.pretty_date(brain.made_active_date)

        review_state = brain.review_state
        listed = review_state == 'public'
        is_pending = review_state == 'pending'

        role = brain.highestTeamRole

        return dict(title=proj_title,
                    proj_id=proj_id,
                    since=mship_activated_on,
                    listed=listed,
                    role=role,
                    is_pending=is_pending,
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
                return brain.lastWorkflowActor == self.context.getId()
            return brain.review_state in self.active_states
        return self._projects_satisfying(is_user_project)

    @property
    @req_memoize
    def invitations(self):
        """ return mship brains for pending project invitations """
        def is_invitation(brain):
            return brain.review_state == 'pending' and \
                   brain.lastWorkflowActor != self.context.getId()
        return self._projects_satisfying(is_invitation)

    @property
    @req_memoize
    def member_requests(self):
        """ return all proj_ids for pending member requests """
        def is_member_request(brain):
            return brain.review_state == 'pending' and \
                   brain.lastWorkflowActor == self.context.getId()
        return self._projects_satisfying(is_member_request)

    def _membership_for_proj(self, proj_id):
        tmtool = self.get_tool('portal_teams')
        team = tmtool.getTeamById(proj_id)
        mem = self.context
        mem_id = mem.getId()
        mship = team._getMembershipByMemberId(mem_id)
        return mship

    def leave_project(self, proj_id):
        """ remove membership by marking the membership object as inactive """
        mship = self._membership_for_proj(proj_id)
        wft = self.get_tool('portal_workflow')
        wft.doActionFor(mship, 'deactivate')

    def change_visibility(self, proj_id):
        """ change whether project members appear in listings """
        mship = self._membership_for_proj(proj_id)
        wft = self.get_tool('portal_workflow')
        cur_state = wft.getInfoFor(mship, 'review_state')
        if cur_state == 'public':
            wft.doActionFor(mship, 'make_private')
        else:
            wft.doActionFor(mship, 'make_public')

    @action('leave')
    def leave_handler(self, targets, fields=None):
        json_ret = {}
        for proj_id in targets:
            self.leave_project(proj_id)
            json_ret[proj_id] = dict(action='delete')
        return json_ret

    @property
    @req_memoize
    def infomsgs(self):
        """info messages re project admission/rejection"""
        # annotation on the member object itself?
        # or maybe should be annotated on the person folder?
        # that's easier, because then it would just be the context
        mem_data = self.get_tool('portal_memberdata')
        mem_id = self.context.getId()
        mem_obj = mem_data._getOb(mem_id)
        annot = IAnnotations(mem_obj)
        return annot.get('infomsgs', [])

    @property
    def n_updates(self):
        return len(self.infomsgs) + len(self.invitations)
