import logging
import re
import string

from zope import event
from zope.interface import implements
from zope.component import getAdapters, queryAdapter
from zope.component import getMultiAdapter
from Acquisition import aq_parent

from topp.featurelets.interfaces import IFeaturelet, IFeatureletSupporter

from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.permissions import DeleteObjects
from plone.memoize.instance import memoizedproperty
from opencore.geocoding.view import getReadGeoViewWrapper
from opencore.geocoding.view import getWriteGeoViewWrapper
from opencore.interfaces.adding import IAddProject
from opencore.interfaces.catalog import IMetadataDictionary 
from opencore.interfaces.event import AfterProjectAddedEvent, \
      AfterSubProjectAddedEvent
from opencore.interfaces.workflow import IReadWorkflowPolicySupport

from opencore.project import PROJ_HOME
from opencore.browser import formhandler
from opencore.browser.base import BaseView, _
from opencore.browser.formhandler import OctopoLite, action
from opencore.project.browser.utils import vdict
from opencore.interfaces import IHomePage
from opencore.nui.wiki.add import get_view_names

from DateTime import DateTime

_marker = object()

logger = logging.getLogger('opencore.project.browser')


class ProjectBaseView(BaseView):

    proj_macros = ZopeTwoPageTemplateFile('macros.pt')

    @memoizedproperty
    def has_mailing_lists(self):
        return self._has_featurelet('listen')

    @memoizedproperty
    def has_task_tracker(self):
        return self._has_featurelet('tasks')

    @memoizedproperty
    def has_blog(self):
        return self._has_featurelet('blog')

    def _has_featurelet(self, flet_id):
        flet_adapter = queryAdapter(
                         IFeatureletSupporter(self.context),
                         IFeaturelet,
                         name=flet_id)
        if flet_adapter is None:
            return False
        return flet_adapter.installed

    @property
    def geo_info(self):
        """geo information for display in forms;
        takes values from request, falls back to existing project
        if possible."""
        ##geo = IReadWriteGeo(self) #XXX This fails in zope 2.9.
        geo = getReadGeoViewWrapper(self)
        return geo.geo_info()
    

class ProjectContentsView(ProjectBaseView, OctopoLite):

    class ContentsCollection(list):
        """
        each item in the list should have a .collection attribute
        which references the Collection itself. doing this by overriding
        methods on the Collection to stick the attribute in when
        adding the item.
        NOTE THAT I AM only overriding select methods so if any other
        method is called the template rendering will break mysteriously!
        """
        def __init__(self, item_type, view, *contents):
            self.item_type = item_type
            self.info = ProjectContentsView.needed_values[item_type]
            self.info.collection = self
            self.editable = view.editable
            self.extend(contents)

        def __setitem__(self, i, y):
            list.__setitem__(self, i, y)
            y.collection = self

        def append(self, item):
            list.append(self, item)
            item.collection = self

        def extend(self, items):
            list.extend(self, items)
            for item in items:
                item.collection = self

    template = ZopeTwoPageTemplateFile('contents.pt')

    item_row = ZopeTwoPageTemplateFile('item_row.pt')
    item_table_snippet = ZopeTwoPageTemplateFile('item_table_snippet.pt')
    item_tbody_snippet = ZopeTwoPageTemplateFile('item_tbody_snippet.pt')
    item_thead_snippet = ZopeTwoPageTemplateFile('item_thead_snippet.pt')

    _portal_type = {'pages': "Document",
                    'lists': "Open Mailing List",
                    'files': ("FileAttachment", "Image")
                    }

    needed_values = dict(pages=vdict("Wiki pages", _editable=True,
                                     obj_date='ModificationDate',
                                     obj_author='lastModifiedAuthor'),
                         files=vdict("Images & Attachments", _editable=True,
                                     obj_date='Date',
                                     obj_author='Creator',
                                     obj_size='getObjSize'),
                         lists=vdict("Mailing lists", _editable=False,
                                     obj_date='Date',
                                     obj_author='Creator',
                                     obj_size='mailing_list_threads'),
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
        obj_dict = type('contents_item', (dict,), {'collection': None})()
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
        return obj_dict

    @memoizedproperty
    def tasktracker_url(self): 
        # XXX todo all this logic prob ought be in opencore.tasktracker.

        loc = self.get_opencore_property('tasktracker_external_uri')

        if loc.startswith('http://'): # XXX todo this is dumb
            return loc
        return "%s/%s" % (self.context.absolute_url(), loc)
        
    @memoizedproperty
    def project_path(self):
        return '/'.join(self.context.getPhysicalPath())

    def _sorted_items(self, item_type, sort_by=None, sort_order='descending'):
        query = dict(portal_type=self._portal_type[item_type],
                     path=self.project_path,
                     sort_on=sort_by,
                     sort_order=sort_order)
        brains = self.catalog(**query)
        needed_values = self.needed_values[item_type]
        ret = self.ContentsCollection(item_type, self)
        for brain in brains:
            ret.append(self._make_dict_and_translate(brain, needed_values))
        if needed_values.editable is False:
            ret.editable = False
        return ret

    @memoizedproperty
    def pages(self):
        objs = self._sorted_items('pages', 'sortable_title')
        return self._filter_objs(objs)

    @memoizedproperty
    def lists(self):
        return self._sorted_items('lists', 'sortable_title')

    @memoizedproperty
    def files(self):
        return self._sorted_items('files', 'sortable_title')

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
        """
        delete the objects referenced by the list of brains passed in.
        returns ([deleted_ids], [failed_nondeleted_ids])

        nowhere does this view code explicitly check that the requesting
        user has delete privileges on the objects that are to be deleted;
        instead it relies on the assumption that the manage_delObjects
        method will perform those security checks. this is true for the
        content types we have, but is not guaranteed to be the case, and
        the view code is trusted, so it would be more conservative to check
        for proper delete permissions right here in the view code. on the
        other hand, this would then mean that the same security check is
        performed twice for all objects that happen to do the check in the
        manage_delObjects code, which is currently all of our objects.

        so, most likely, i imagine that awareness of the issue is sufficient.
        """
        parents = {}
        collateral_damage = {}

        surviving_objects = []
        deleted_objects = []
        
        if not brains:
            self.add_status_message(_(u'psm_no_items_to_delete',
                                      u'Please select items to delete.'))

        # put obj ids in dict keyed on their parents for optimal batch deletion
        for brain in brains:                
            parent_path, brain_id = brain.getPath().rsplit('/', 1)
            parent_path = parent_path.split(self.project_path, 1)[-1].strip('/')
            parents.setdefault(parent_path, []).append(brain_id)
            
            type = brain.portal_type
            ### our Documents are currently folderish 
            # and sometimes contain file-like things.
            # Any child files will be deleted by this
            # operation, so we need to tell the client
            # that we deleted these files as well
            if type == 'Document':
                file_type = self._portal_type['files']
                child_files = [b.getId for b in 
                               self.catalog(portal_type=file_type,
                                            path=brain.getPath())]
                if child_files:
                    collateral_damage.setdefault(brain_id, []).extend(child_files)

        # delete objs in batches per parent obj
        for parent, child_ids in parents.items():
            if child_ids:
                if not parent:
                    parent = self.context
                else:
                    parent = self.context.restrictedTraverse(parent)
                deletees = list(child_ids)
                parent.manage_delObjects(child_ids)  ## dels ids from list as objs are deleted
            if child_ids: # deletion failed for some objects
                surviving_objects.extend(child_ids)  ## what's left in 'child_ids' was not deleted
                deleted_objects.extend([oid for oid in deletees
                                        if oid not in child_ids]) ## the difference btn deletees and child_ids == deleted
            else: # deletion succeeded for every object
                deleted_objects.extend(deletees)
        
        # if any additional objects (ie file attachments) were deleted
        # as a consequence, add them to deleted_objects too
        if collateral_damage: 
            for oid in deleted_objects:
                extra = collateral_damage.get(oid)
                if extra: deleted_objects.extend(extra)

        return (deleted_objects, surviving_objects)

    def show_deletes(self):
        # XXX this is a speed hack for #1158,
        # delete button is only shown for
        # project members, it is not
        # fine grained.
        return 'ProjectMember' in self.context.getTeamRolesForAuthMember()

    def _filter_objs(self, objs):
        # Mark stuff that can't be edited or deleted.  This is another
        # speed hack to handle bugs 1330 (and 1158 via show_deletes())
        # but again, we don't check security on each object.
        show_deletes = self.show_deletes()
        for d in objs:
            if d['id'] == PROJ_HOME:
                d['uneditable'] = True
                d['undeletable'] = True
            if not show_deletes:
                d['undeletable'] = True
        return objs

    def _resort(self, item_type, sort_by=None, sort_order=None):
        sort_by = self.needed_values[item_type].sortable(sort_by)
        new_objs = self._sorted_items(item_type, sort_by, sort_order)
        return self._filter_objs(new_objs)

    @action('resort')
    def resort(self, sources, fields=None):
        item_type = self.request.form.get("item_type")
        if item_type not in self._portal_type:
            return False

        sort_by = self.request.form.get("sort_by")
        sort_order = self.request.form.get("sort_order")
        items = self._resort(item_type, sort_by, sort_order)

        if sort_order == 'ascending':
            sort_order = 'descending'
        else:
            sort_order = 'ascending'

        thead_obj = {'html': self.item_thead_snippet(item_type=item_type,
                                                     item_date_author_header=(item_type=='pages' and "Last Modified" or "Created"),
                                                     sort_on=sort_by,
                                                     sort_order=sort_order,
                                                     item_collection=items
                                                     ),
                     'effects': '',
                     'action': 'replace'
                     }
        tbody_obj = {'html': self.item_tbody_snippet(item_collection=items),
                     'effects': 'highlight',
                     'action': 'replace'
                     }
        
        return {'oc-%s-tbody' % item_type: tbody_obj,
                'oc-%s-thead' % item_type: thead_obj
                }

    @action('delete')
    def delete_items(self, sources, fields=None):
        item_type = self.request.form.get("item_type")

        if item_type == 'pages' and PROJ_HOME in sources:
            sources.remove("project-home")

        brains = self.catalog(id=sources, path=self.project_path)

        deletions, survivors = self._delete(brains)
        # for now we'll only return the deleted obj ids. later we may return the survivors too.
        commands = {}
        for obj_id in deletions:
            commands[obj_id] = {
                'action': 'delete'
                }
        return commands

    @action('update')
    def update_items(self, sources, fields=None):
        item_type = self.request.form.get("item_type")

        if item_type == 'pages' and PROJ_HOME in sources:
            sources.remove("project-home")

        brains = self.catalog(id=sources, path=self.project_path)

        snippets = {}
        objects = dict([(b.getId, b.getObject()) for b in brains])

        for old, new in zip(sources, fields):
            page = objects[old]
            page.setTitle(new['title'])
            page.reindexObject(('Title',))
            snippets[page.getId()] = {
                'html': self.item_row(
                    item=self._make_dict_and_translate(
                        page,
                        self.needed_values[item_type]),
                    item_type=item_type),
                'effects': 'highlight',
                'action': 'replace'
                }
        return snippets



class ProjectPreferencesView(ProjectBaseView, OctopoLite):

    template = ZopeTwoPageTemplateFile('preferences.pt')
    logo_snippet = ZopeTwoPageTemplateFile('logo-snippet.pt')
        
    def mangled_logo_url(self):
        """When a project logo is changed, the logo_url remains the same.
        This method appends a timestamp to logo_url to trick the browser into
        fetching the new image instead of using the cached one which could be --
        out of date (and always will be in the ajaxy case).
        """
        logo = self.context.getLogo()
        if logo:
            timestamp = str(DateTime()).replace(' ', '_')
            return '%s?%s' % (logo.absolute_url(), timestamp)
        return self.defaultProjLogoURL


    @action("uploadAndUpdate")
    def change_logo(self, target=None, fields=None):
        logo = self.request.form.get("logo")

        if not self.check_logo(logo):
            return

        self.context.reindexObject('logo')
        return {
            'oc-project-logo' : {
                'html': self.logo_snippet(),
                'action': 'replace',
                'effects': 'highlight'
                }
            }

    def check_logo(self, logo):
        try:
            self.context.setLogo(logo)
        except ValueError: # must have tried to upload an unsupported filetype
            self.addPortalStatusMessage('Please choose an image in gif, jpeg, png, or bmp format.')
            return False
        return True


    @action("remove")
    def remove_logo(self, target=None, fields=None):
        proj = self.context
        proj.setLogo("DELETE_IMAGE")  # blame the AT API
        proj.reindexObject('logo')
        return {
                'oc-project-logo' : {
                    'html': self.logo_snippet(),
                    'action': 'replace',
                    'effects': 'highlight'
                    }
                }


    @formhandler.button('update')
    def handle_request(self):
        title = self.request.form.get('title')
        title = strip_extra_whitespace(title)
        self.request.form['title'] = title
        if not valid_project_title(title):
            self.errors['title'] = _(u'err_project_name', u'The project name must contain at least 2 characters with at least 1 letter or number.')

        coords = self.geocode_from_form()

        if self.errors:
            self.add_status_message(_(u'psm_correct_errors_below', u'Please correct the errors indicated below.'))
            return

        allowed_params = set(['__initialize_project__', 'update', 'set_flets',
                              'title', 'description', 'logo', 'workflow_policy',
                              'featurelets', 'home-page',
                              'location', 'position-text'])
        new_form = {}
        for k in allowed_params:
            if k in self.request.form:
                new_form[k] = self.request.form[k]

        reader = IReadWorkflowPolicySupport(self.context)
        old_workflow_policy = reader.getCurrentPolicyId()

        logo = new_form.get('logo')
        logochanged = False
        if logo:
            if not self.check_logo(logo):
                return
            logochanged = True
            del self.request.form['logo'], new_form['logo']

        locationchanged = False
        if getWriteGeoViewWrapper(self).set_geolocation(coords):
            locationchanged = True
        elif self.context.getLocation() != new_form.get('location', ''):
            locationchanged = True

        #display change status of flet, security, title, description, logo.
        changed = {
            _(u'psm_project_title_changed', u"The title has been changed.") : self.context.title != new_form.get('title', self.context.title),
            _(u'psm_project_desc_changed', u"The description has been changed.") : self.context.description != new_form.get('description', self.context.description),
            _(u'psm_project_logo_changed', u"The project image has been changed.") : logochanged,
            _(u'psm_security_changed', u"The security policy has been changed.") : old_workflow_policy != new_form.get('workflow_policy', old_workflow_policy),
            _(u'psm_location_changed', u"The location has been changed."): locationchanged,
            }

        supporter = IFeatureletSupporter(self.context)
        flets = [f for n, f in getAdapters((supporter,), IFeaturelet)]

        old_featurelets = set([(f.id, f.title) for f in flets if f.installed])
            
        self.request.form = new_form
        self.context.processForm(REQUEST=self.request, metadata=1)
        featurelets = set([(f.id, f.title) for f in flets if f.installed])

        for flet in featurelets:
            if flet not in old_featurelets:
                changed[_(u'psm_featurelet_added', u'${flet} feature has been added.',
                          mapping={u'flet':flet[1].capitalize()})] = 1
        
        for flet in old_featurelets:
            if flet not in featurelets:
                changed[_(u'psm_featurelet_removed', u'${flet} feature has been removed.',
                          mapping={u'flet':flet[1].capitalize()})] = 1

        
        for field, changed in changed.items():
            if changed:
                self.add_status_message(field)

        home_page = self.request.form.get('home-page', None)
        hpcontext = IHomePage(self.context)
        if home_page is not None:
            if hpcontext.home_page != home_page:
                hp_url = '%s/%s' % (self.context.absolute_url(), home_page)
                self.add_status_message(_(u'psm_proj_homepage_change', u'Project home page set to: <a href="${hp_url}">${homepage}</a>',
                                        mapping={u'homepage':home_page, u'hp_url':hp_url}))
                hpcontext.home_page = home_page


        self.redirect(self.context.absolute_url())

    def current_home_page(self):
        return IHomePage(self.context).home_page

    def featurelets(self, include_wiki=False):
        supporter = IFeatureletSupporter(self.context)
        all_flets = [flet for name, flet in getAdapters((supporter,), IFeaturelet)]
        installed_flets = [flet.id for flet in all_flets if flet.installed]
        flet_data = [dict(id=f.id,
                          title=f.title,
                          url=f._info['menu_items'][0]['action'],
                          checked=f.id in installed_flets,
                          )
                     for f in all_flets]
        if include_wiki:
            flet_data.insert(0, dict(id='wiki',
                                     title='Wiki pages',
                                     url=PROJ_HOME,
                                     checked='True',
                                     ))
        return flet_data
                

class ProjectAddView(ProjectBaseView, OctopoLite):

    template = ZopeTwoPageTemplateFile('create.pt')

    def reserved_names(self):
        return list(get_view_names(self.context)) + ['people', 'projects']

    @action('validate')
    def validate(self, target=None, fields=None):
        putils = getToolByName(self.context, 'plone_utils')
        errors = {}
        id_ = self.request.form.get('projid')
        id_ = putils.normalizeString(id_)
        if (self.context.has_key(id_)
            or id_ in self.reserved_names()):
            errors['oc-id-error'] = {
                'html': 'The requested url is already taken.',
                'action': 'copy',
                'effects': 'highlight'
                }
        else:
            errors['oc-id-error'] = {
                'html': '',
                'action': 'copy',
                'effects': ''
                }
        return errors


    def check_logo(self, project, logo):
        try:
            project.setLogo(logo)
        except ValueError: # must have tried to upload an unsupported filetype
            self.addPortalStatusMessage('Please choose an image in gif, jpeg, png, or bmp format.')
            return False
        return True



    @action('add')
    def handle_request(self, target=None, fields=None):
        putils = getToolByName(self.context, 'plone_utils')
        self.request.set('__initialize_project__', True)

        self.errors = {}
        title = self.request.form.get('title')
        title = strip_extra_whitespace(title)
        if not isinstance(title, unicode):
            title = unicode(title, 'utf-8')
        self.request.form['title'] = title
        if not valid_project_title(title):
            self.errors['title'] = 'The project name must contain ' \
              'at least 2 characters with at least 1 letter or number.'

        id_ = self.request.form.get('projid')
        if not valid_project_id(id_):
            self.errors['id'] = 'The project url may contain only letters, numbers, hyphens, or underscores and must have at least 1 letter or number.'
        else:
            id_ = putils.normalizeString(id_)
            if self.context.has_key(id_):
                self.errors['id'] = 'The requested url is already taken.'

        coords = self.geocode_from_form()

        # not calling validate because it explodes on "'" for project titles
        # XXX is no validation better than an occasional ugly error?
        #proj.validate(REQUEST=self.request, errors=self.errors, data=1, metadata=0)
        if self.errors:
            self.add_status_message(_(u'psm_correct_errors_below', u'Please correct the errors indicated below.'))
            return 
        if id_ in self.reserved_names():
            self.add_status_message(_(u'psm_project_name_reserved', u'The name "${project_name}" is reserved. Please try a different name.',
                                      mapping={u'project_name':id_}))
            self.redirect('%s/create' % self.context.absolute_url())
            return

        proj = self.context.restrictedTraverse('portal_factory/OpenProject/%s' %id_)

        self.context.portal_factory.doCreate(proj, id_)
        proj = self.context._getOb(id_)
        self.notify(proj)

        logo = self.request.form.get('logo')
        if logo:
            if not self.check_logo(proj, logo):
                return
            del self.request.form['logo']

        getWriteGeoViewWrapper(self, proj).set_geolocation(coords)

        self.template = None
        proj_edit_url = '%s/projects/%s/project-home/edit' % (self.siteURL, id_)

        home_page = self.request.form.get('home-page', None)
        if home_page is not None:
            IHomePage(proj).home_page = home_page

        s_message_mapping = {'title': title, 'proj_edit_url': proj_edit_url}


        s_message = _(u'project_created',
                      u'"${title}" has been created. Create a team by searching for other members to invite to your project, then <a href="${proj_edit_url}">edit your project home page</a>.',
                      mapping=s_message_mapping)
        
#        self.add_status_message(s_message)

        self.redirect('%s/tour' % proj.absolute_url())

    def notify(self, project):
        event.notify(AfterProjectAddedEvent(project, self.request))

    def featurelets(self, include_wiki=False):
        # create a stub object that provides IFeatureletSupporter
        # is there a better way to get the list of adapters without having
        # the "for" object?
        class DummyFeatureletSupporter(object):
            implements(IFeatureletSupporter)

        obj = DummyFeatureletSupporter()
        flets = getAdapters((obj,), IFeaturelet)
        flet_data = [dict(id=f.id,
                          title=f.title,
                          url=f._info['menu_items'][0]['action'],
                          checked=False,
                          )
                     for name, f in flets]
        if include_wiki:
            flet_data.insert(0, dict(id='wiki',
                                     title='Wiki pages',
                                     url=PROJ_HOME,
                                     checked='True',
                                     ))
        return flet_data


class RedirectView(BaseView):
    """redirect to the project home page url"""

    def __call__(self):
        hp = IHomePage(self.context).home_page
        url = '%s/%s' % (self.context.absolute_url(), hp)
        self.redirect(url)

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


whitespace_pattern = re.compile('\s+')
def strip_extra_whitespace(title):
    if title is None:
        return ''
    title = whitespace_pattern.sub(' ', title).strip()
    return title.strip()

def valid_project_title(title):
    """
    Alphanumeric is ok with punctuation and whitespace::
    
    >>> valid_project_title('title 1!')
    True

    Unicode is ok (though you will get an ugly id)::

    >>> valid_project_title('\xe6\x97\xa5\xe6\x9c\xac\xe8\xaa\x9e')
    True

    Punctuation is a no go::

    >>> valid_project_title('"!"& ^"")""')
    False

    As is whitespace::

    >>> valid_project_title('\t ')
    False

    """
    if len(title) < 2: return False
    for c in title:
        if not _ignore.get(c):
            if c.isalnum(): # catch alphanumerics
                return True
            if not _printable.get(c): # catch unicode chars but not
                                     # whitespace or escapes
                return True

    return False

class TourView(ProjectBaseView):
    """ dummy view for the 1 page tour """

_ignore = dict((char, True) for char in ''.join((string.punctuation, string.whitespace)))
_printable = dict((char, True) for char in string.printable)

def valid_project_id(id):
    # projects ids are more strict than titles
    if not valid_project_title(id): return False

    valid_chars = string.letters + string.digits + '-_'
    for c in id:
        if c not in valid_chars:
            return False
    return True
