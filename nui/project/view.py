from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import transaction_note
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from opencore.interfaces.event import AfterProjectAddedEvent #, AfterSubProjectAddedEvent
from opencore.nui.base import BaseView, button
from opencore.nui.main import SearchView
from zExceptions import BadRequest
from zExceptions import Redirect
from zope import event


class ProjectPreferencesView(BaseView):

    @button('update')
    def handle_request(self):
        self.context.validate(REQUEST=self.request, errors=self.errors, data=1, metadata=0)
        if not self.errors:
            self.context.processForm(REQUEST=self.request)
            self.redirect(self.context.absolute_url())


class ProjectAddView(BaseView):

    @button('add')
    def handle_request(self):
        putils = getToolByName(self.context, 'plone_utils')
        self.request.set('__initialize_project__', True)

        self.errors = {}
        if not self.request.get('full_name'):
            self.errors['full_name'] = 'Please add a full name'

        title = self.request.form.get('title')
        if not title:
            self.errors['title'] = 'You need to enter a short name for the project'
        id_ = putils.normalizeString(title)
        if self.context.has_key(id_):
            self.errors = {'title' : 'The requested short name is already taken.'}

        if self.errors:
            self.addPortalStatusMessage(u'Please correct the indicated errors.')
            return 

        proj = self.context.restrictedTraverse('portal_factory/OpenProject/%s' %id_)
        proj.validate(REQUEST=self.request, errors=self.errors, data=1, metadata=0)
        if self.errors:
            transaction_note('Started creation of project: %s' %title)
            self.addPortalStatusMessage(u'Please correct the indicated errors.')
            return 

        self.context.portal_factory.doCreate(proj, id_)
        proj = self.context._getOb(id_)
        event.notify(AfterProjectAddedEvent(proj, self.request))
        transaction_note('Finished creation of project: %s' %title)
        self.redirect(proj.absolute_url())


class ProjectTeamView(SearchView):

    def __init__(self, context, request):
        SearchView.__init__(self, context, request)
        self.sort_by = None
   
    @button('sort')
    def handle_request(self):
        self.sort_by = self.request.get('sort_by', None)

    @property
    def memberships(self):
        project = self.context
        teams = project.getTeams()
        assert len(teams) == 1
        team = teams[0]
        team_path = '/'.join(team.getPhysicalPath())
        active_states = team.getActiveStates()

        if self.sort_by == 'location':
            #sort by username
            query = dict(portal_type='OpenMembership',
                     path=team_path,
                     review_state=active_states,
                     )
            mem_brains = self.catalog(**query)
            mem_ids = [mem_brain.getId for mem_brain in mem_brains]
            query = dict(sort_on='sortableLocation',
                         getId=mem_ids,
                         )
            mem_brains = self.membranetool(**query)
            

        elif self.sort_by == 'membership_date':
            mem_brains = []
        elif self.sort_by == 'contributions':
            mem_brains = []
        else:
            #sort by username
            query = dict(portal_type='OpenMembership',
                     path=team_path,
                     review_state=active_states,
                     )
            mem_brains = self.catalog(**query)

            ids = [b.getId for b in mem_brains]
            query = dict(portal_type='OpenMember',
                         getId=ids,
                         sort_on='getId',
                         )
            mem_brains = self.membranetool(**query)

        return self._get_batch(mem_brains)
            
    def projects_for_member(self, member):
        # XXX these should be brains
        projects = self._projects_for_member(member)
        # only return max 10 results
        return projects[:10]

    def more_than_ten_projects(self, member):
        projects = self._projects_for_member(member)
        return len(projects) > 10

#    @memoized
    def _projects_for_member(self, member):
        return member.getProjects()
