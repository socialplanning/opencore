from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import transaction_note
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from opencore.nui.base import BaseView, button
from opencore.nui.formhandler import OctopoLite, action
from zExceptions import BadRequest
from zExceptions import Redirect
from zope import event
from topp.utils.pretty_date import prettyDate
from datetime import datetime

        
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
        usr = self.viewedmember()
        portrait = self.request.form.get('portrait')
        mode = self.request.form.get('mode')
              
        # TODO resize portrait if necessary

        if mode == 'async':
            if portrait:
                usr.setPortrait(portrait)
            else: # TODO detect whether to delete more explicitly. currently the
                  # remove portrait button is identical in name and value to the
                  # change portrait button, so this relies on the user not having
                  # clicked browse and selecting an image first. consult egj/nickyg
                usr._delOb('portrait')
            usr.reindexObject()
            return { 'oc-profile-avatar' : self.portrait_snippet()}

        else:
            for field, value in self.request.form.items():
                mutator = 'set%s' % field.capitalize()
                mutator = getattr(usr, mutator, None)
                if mutator is not None:
                    mutator(value)
                self.user_updated()
    
            usr.reindexObject()
            return self.redirect('profile')


    def user_updated(self): # TODO
        """callback to tell taggerstore a user updated (possibly) taggifiable
        fields. something like a POST to /taggerstore/."""
        pass


class MemberPreferences(BaseView, OctopoLite):

    template = ZopeTwoPageTemplateFile('preferences.pt')

    def _mship_brains_for(self, mem):
        active_states = ['public', 'private']
        user_id = mem.getId()
        query = dict(portal_type='OpenMembership',
                     review_state=active_states,
                     getId=user_id,
                     )
        mships = self.catalogtool(**query)
        return mships

    def _mship_brains(self):
        return self._mship_brains_for(self.context)

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

    def _create_project_dict(self, brain):
        project_id = self._project_id_from(brain)
        project_info = self._project_metadata_for(project_id)
        proj_title = project_info['Title']
        proj_id = project_info['getId']

        mship_activated_on = self.pretty_date(brain.made_active_date)

        review_state = brain.review_state
        listed = review_state == 'public'

        return dict(title=proj_title,
                    proj_id=proj_id,
                    since=mship_activated_on,
                    listed=listed,
                    )

    def get_projects_for_user(self):
        mships = self._mship_brains()
        project_dicts = map(self._create_project_dict, mships)
        return project_dicts

    def _pending_mships(self, mem_id):
        query = dict(portal_type='OpenMembership',
                     getId=mem_id,
                     review_state='pending')
        mship_brains = self.catalogtool(**query)
        return mship_brains
        return map(self._project_id_from, mship_brains)

    def _pending_mships_satisfying(self, mem_id, pred):
        pending_brains = self._pending_mships(mem_id)
        invitation_brains = (b for b in pending_brains
                             if pred(b))
        return [self._project_id_from(b)
                for b in invitation_brains]

    def invitations(self):
        """ return all proj_ids for pending project invitations """
        mem_id = self.context.getId()
        pred = lambda b: b.lastWorkflowActor != mem_id
        return self._pending_mships_satisfying(mem_id, pred)

    def member_requests(self):
        """ return all proj_ids for pending member requests """
        mem_id = self.context.getId()
        pred = lambda b: b.lastWorkflowActor == mem_id
        return self._pending_mships_satisfying(mem_id, pred)

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

    def project_for(self, proj_id):
        return self.portal.projects._getOb(proj_id)
