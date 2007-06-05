from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import transaction_note
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from opencore.interfaces.event import AfterProjectAddedEvent #, AfterSubProjectAddedEvent
from opencore.nui.base import BaseView, button
from opencore.nui.main import SearchView
from zExceptions import BadRequest
from zExceptions import Redirect
from zope import event
from plone.memoize.view import memoize
from plone.memoize.view import memoize_contextless

class ProjectContentsView(BaseView):
    
    def __call__(self):
        import pdb; pdb.set_trace()

    def rename_wiki_pages(self, from_ids, to_ids):
        # need to change their title as well as their id
        for old, new in zip(from_ids, to_ids):
            page = self.context.restrictedTraverse(old)
            page.setTitle(new)
        # XXX we might get rid of the line below and only setTitles
        self.context.manage_renameObjects(from_ids, to_ids)

    def delete_wiki_pages(self, ids):
        self.context.manage_delObjects(ids)

    def get_wiki_pages(self):
        return self.catalog(portal_type="Document",
                            path='/'.join(self.context.getPhysicalPath()))

    def rename_attachments_and_images(self, from_ids, to_ids):
        for old, new in zip(from_ids, to_ids):
            file = self.context.restrictedTraverse(old)
            file.setTitle(new)

    def delete_attachments_and_images(self, ids):
        self.context.manage_delObjects(ids)

    def get_attachments_and_images(self):
        return self.catalog(portal_type=("FileAttachment","Image"),
                            path='/'.join(self.context.getPhysicalPath()))

    def rename_mailing_lists(self, from_ids, to_ids):
        list_folder = self.context.lists
        for old, new in zip(from_ids, to_ids):
            list = list_folder.restrictedTraverse(old)
            list.setTitle(new)
        # XXX we might get rid of the line below and only setTitles
        list_folder.manage_renameObjects(from_ids, to_ids)

    def delete_mailing_lists(self, ids):
        self.context.lists.manage_delObjects(ids)

    def get_mailing_lists(self):
        return self.catalog(portal_type="Open Mailing List",
                            path='/'.join(self.context.getPhysicalPath()))


class ProjectPreferencesView(BaseView):

    @button('update')
    def handle_request(self):
        self.context.validate(REQUEST=self.request,
                              errors=self.errors, data=1, metadata=0)
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
        project = self.context
        teams = project.getTeams()
        assert len(teams) == 1
        team = teams[0]
        self.team_path = '/'.join(team.getPhysicalPath())
        self.active_states = team.getActiveStates()
        self.sort_by = None
   
    @button('sort')
    def handle_request(self):
        self.sort_by = self.request.get('sort_by', None)

    def handle_sort_membership_date(self):
        query = dict(portal_type='OpenMembership',
                 path=self.team_path,
                 review_state=self.active_states,
                 sort_on='made_active_date',
                 sort_order='descending',
                 )
        membership_brains = self.catalog(**query)
        mem_ids = [b.getId for b in membership_brains]
        query = dict(portal_type='OpenMember',
                     getId=mem_ids,
                     )
        member_brains = self.membranetool(**query)
        lookup_dict = dict((b.getId, b) for b in member_brains)

        results = [lookup_dict.get(b.getId, None) for b in membership_brains]
        # filter out None's, which appear for admins that are not openmembers
        results = filter(None, results)
        return self._get_batch(results)

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
        results = self.membranetool(**query)
        return self._get_batch(results)

    def handle_sort_contributions(self):
        return self._get_batch([])

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
        return self._get_batch(results)

    @property
    @memoize
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

    def more_than_ten_projects(self, member):
        projects = self._projects_for_member(member)
        return len(projects) > 10

    @memoize_contextless
    def _projects_for_member(self, member):
        return member.getProjects()

    def membership_info_for(self, member):
        mem_id = member.getId()
        project = self.context
        project_id = project.getId()
        portal_teams = getToolByName(self.context, 'portal_teams')
        team = portal_teams._getOb(project_id)
        membership = team._getOb(mem_id)

        contributions = 'XXX'
        activation = self.pretty_date(membership.made_active_date)
        modification = self.pretty_date(membership.ModificationDate())
        return dict(contributions=contributions,
                    activation=activation,
                    modification=modification,
                    )
