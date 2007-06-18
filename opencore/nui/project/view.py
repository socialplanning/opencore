from zope import event
from zope.component import getMultiAdapter
from zExceptions import BadRequest, Redirect
from Acquisition import aq_parent

from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.permissions import DeleteObjects
from Products.CMFPlone.utils import transaction_note
from plone.memoize.instance import memoize, memoizedproperty
from plone.memoize.view import memoize_contextless
from plone.memoize.view import memoize as req_memoize

from opencore.interfaces import IAddProject, IAddSubProject
from opencore.interfaces.catalog import IMetadataDictionary 
from opencore.interfaces.event import AfterProjectAddedEvent, \
      AfterSubProjectAddedEvent

from opencore.project.utils import get_featurelets
from opencore.tasktracker import uri as tt_uri
from opencore.content.membership import OpenMembership

from opencore.nui import formhandler
from opencore.nui.base import BaseView
from opencore.nui.main import SearchView

_marker = object()

def vdict(**extra): 
    base=dict(id='getId',
              title='Title',
              url='getURL',
              )
    base.update(extra)
    return base 

class ProjectContentsView(BaseView):

    contents_row_snippet = ZopeTwoPageTemplateFile('item_row.pt')
    item_table_snippet = ZopeTwoPageTemplateFile('item_table_snippet.pt')

    _portal_type = {'pages': "Document",
                    'lists': "Open Mailing List",
                    'files': ("FileAttachment", "Image")
                    }

    needed_values = dict(pages=vdict(obj_date='ModificationDate',
                                     obj_author='lastModifiedAuthor'),
                         files=vdict(obj_date='Date',
                                     obj_author='Creator',
                                     obj_size='getObjSize'),
                         lists=vdict(obj_date='Date',
                                     obj_author='Creator',
                                     obj_size='getObjSize'),
                         )

    def retrieve_metadata(self, obj):
        ## DWM: not sure adaptation gives a real advantage here
        try:
            metadata = IMetadataDictionary(obj)
        except TypeError:
            metadata = getMultiAdapter((obj, self.catalog), IMetadataDictionary)
        return metadata

    def _make_dict_and_translate(self, obj, needed_values):
        # could probably fold this map a bit
        obj_dict = {}
        metadata = self.retrieve_metadata(obj)
        
        for field in needed_values: # loop through fields that we need
            val=_marker
            val = metadata.get(needed_values[field], _marker)
            if 'date' in field:
                val = self.pretty_date(val)
            if val is not _marker:
                obj_dict[field] = val
            else:
                raise KeyError("field is missing: %s -- %s" %(field, obj))
##                 continue
            
##             has_accessor = False
##             for obj_field in needed_values[field]: # loop through object-specific ways of getting the field
##                 if hasattr(obj, obj_field):
##                     val = getattr(obj, obj_field)
##                     has_accessor = True
##                     break
                
##             if not has_accessor:
##                 raise Exception("Could not fetch a %s value from the object %s among the accessors %s!" % (
##                         field, obj, list(needed_values[field])))
##             if callable(val): val = val()
##             if 'date' in field: val = self.pretty_date(val)  # would be fun to genericize this and pass in
##             obj_dict[field] = val
        return obj_dict

    @memoizedproperty
    def has_mailing_lists(self):
        return self._has_featurelet('listen')

    @memoizedproperty
    def has_task_tracker(self):
        return self._has_featurelet('tasks')

    @memoizedproperty
    def tasktracker_url(self): 
        # XXX todo all this logic prob ought be in opencore.tasktracker.

        loc = tt_uri.get_external_uri()

        if loc.startswith('http://'): # XXX todo this is dumb
            return loc
        return "%s/%s" % (self.context.absolute_url(), loc)
        
    def _has_featurelet(self, flet_id):
        flets = get_featurelets(self.context)
        for flet in flets:
            if flet['name'] == flet_id:
                return True
        return False

    @memoizedproperty
    def project_path(self):
        return '/'.join(self.context.getPhysicalPath())

    def _sorted_items(self, item_type, sort_by=None):
        brains = self.catalog(portal_type=self._portal_type[item_type],
                              path=self.project_path,
                              sort_on=sort_by)
        needed_values = self.needed_values[item_type]
        ret = []
        for brain in brains:
            ret.append(self._make_dict_and_translate(brain, needed_values))
        return ret

    @memoizedproperty
    def pages(self):
        objs = self._sorted_items('pages')
        for d in objs:
            if d['id'] == 'project-home':
                d['uneditable'] = True
        return objs

    @memoizedproperty
    def lists(self):
        return self._sorted_items('lists')

    @memoizedproperty
    def files(self):
        return self._sorted_items('files')

    @memoizedproperty
    def editable(self):
        mtool = getToolByName(self.context, 'portal_membership')
        return bool(mtool.checkPermission(DeleteObjects, self.context))

    def _make_dict(self, obj, needed_values):
        obj_dict = {}
        for field in needed_values:
            val = getattr(obj, field, None)
            if val is None: continue
            if callable(val): val = val()
            obj_dict[field] = val
        return obj_dict

    def _delete(self, brains):
        parents = {}
        surviving_children = []
        for brain in brains:
            parent_path, brain_id = brain.getPath().rsplit('/', 1)
            parent_path = parent_path.split(self.project_path, 1)[-1].strip('/')
            parents.setdefault(parent_path, []).append(brain_id)
        for parent, child_ids in parents.items():
            if child_ids:
                if not parent:
                    parent = self.context
                else:
                    parent = self.context.restrictedTraverse(parent)
                parent.manage_delObjects(child_ids)
            if child_ids: # deletion failed, we've a problem
                surviving_children.extend(child_ids)
        return surviving_children

    def resort(self):
        """ don't use this yet """
        item_type = self.request.form.get("item_type")
        if item_type not in self._portal_type: return

        sort_by = self.request.form.get("sort_by")
        
        items = self._sorted_items(item_type, sort_by)
        return self.item_table_snippet(items=items, item_type=item_type)

    @formhandler.octopus
    def modify_contents(self, action, sources, fields=None):
        item_type = self.request.form.get("item_type")

        if item_type == 'pages' and 'project-home' in sources:
            sources.remove("project-home")

        brains = self.catalog(id=sources, path=self.project_path)

        if action == 'delete':
            survivors = self._delete(brains)
            # return a list of all successfully deleted items
            if survivors:
                return list(set(sources).difference(survivors))
            return sources

        elif action == 'update': # @@ move out to own method to optimize
            snippets = {}
            objects = dict([(b.getId, b.getObject()) for b in brains])
            for old, new in zip(sources, fields):
                page = objects[old]
                page.setTitle(new['title'])
                page.reindexObject(('Title',))
                snippets[page.getId()] = self.contents_row_snippet(
                    item=self._make_dict_and_translate(page,
                                                       self.needed_values[item_type]),
                    item_type=item_type)
            
            return snippets

class ProjectPreferencesView(BaseView):
        
    @formhandler.button('update')
    def handle_request(self):
        self.context.validate(REQUEST=self.request,
                              errors=self.errors, data=1, metadata=0)
        if not self.errors:
            self.context.processForm(REQUEST=self.request)
            self.redirect(self.context.absolute_url())


class ProjectAddView(BaseView):

    @formhandler.button('add')
    def handle_request(self):
        putils = getToolByName(self.context, 'plone_utils')
        self.request.set('__initialize_project__', True)

        self.errors = {}
        if not self.request.get('full_name'):
            self.errors['full_name'] = 'Project requires a full name.'

        title = self.request.form.get('title')
        if not title:
            self.errors['title'] = 'Project requires a url.'
        id_ = putils.normalizeString(title)
        if self.context.has_key(id_):
            self.errors = {'title' : 'The requested url is already taken.'}

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
        self.notify(proj)
        transaction_note('Finished creation of project: %s' %title)
        self.redirect(proj.absolute_url())

    def notify(self, project):
        event.notify(AfterProjectAddedEvent(project, self.request))



class SubProjectAddView(ProjectAddView):

    def __init__(self, context, request):
        self.parent_project = context
        fake_ctx = self.find_project_container(context, request)
        ProjectAddView.__init__(self, fake_ctx, request)

    def find_project_container(self, obj, request):
        cur = obj
        while cur is not None and not IAddProject.providedBy(cur):
            cur = aq_parent(obj)
        return cur
    
    def notify(self, project): 
        event.notify(AfterSubProjectAddedEvent(project,
                                               self.parent_project,
                                               self.request))

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


class ProjectTeamView(TeamRelatedView):
   
    @formhandler.button('sort')
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
        lookup_dict = dict((b.getId, b) for b in member_brains if b.getId)

        return self._get_batch(lookup_dict.get(b.getId) for b in membership_brains)

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
        team = self.team
        membership = team._getOb(mem_id)

        contributions = 'XXX'
        activation = self.pretty_date(membership.made_active_date)
        modification = self.pretty_date(membership.ModificationDate())
        return dict(contributions=contributions,
                    activation=activation,
                    modification=modification,
                    )

class ManageTeamView(TeamRelatedView):
    """
    View class for the team management screens.
    """
    team_manage_macros = ZopeTwoPageTemplateFile('team-manage-macros.pt')
    mship_type = OpenMembership.portal_type
    rolemap = {'ProjectAdmin': 'admin',
               'ProjectMember': 'member',
               }

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
    def active_mships(self):
        cat = self.get_tool('portal_catalog')
        mem_ids = self.team.getActiveMemberIds()
        brains = cat(portal_type=self.mship_type,
                     path=self.team_path,
                     id=mem_ids)
        mships = []
        for brain in brains:
            data = {'id': brain.id,
                    'getId': brain.getId,
                    'review_state': brain.review_state,
                    }

            made_active_date = brain.made_active_date
            if not made_active_date:
                made_active_date = brain.CreationDate
            data['active_since'] = made_active_date

            role = self.team.getHighestTeamRoleForMember(brain.id)
            data['role'] = self.rolemap[role]
            mships.append(data)
        return mships

    def getMemberURL(self, mem_id):
        mtool = self.get_tool('portal_membership')
        return mtool.getHomeUrl(mem_id)
