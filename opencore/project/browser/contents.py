from Products.CMFCore.permissions import DeleteObjects, ModifyPortalContent
from Products.CMFCore.utils import getToolByName
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from Products.ZCatalog.Catalog import AbstractCatalogBrain
from opencore.browser.formhandler import OctopoLite, action
from opencore.i18n import _
from opencore.nui import indexing
from opencore.project import PROJ_HOME
from opencore.project.browser.base import ProjectBaseView
from opencore.project.browser.utils import vdict
from opencore.utility.interfaces import IProvideSiteConfig
from plone.memoize.instance import memoize, memoizedproperty
from opencore.browser import tal
from zope.component import getUtility
from zExceptions import BadRequest
import ZTUtils

_marker = object()


class ProjectContentsView(ProjectBaseView, OctopoLite):

    template = ZopeTwoPageTemplateFile('contents.pt')

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
        if isinstance(obj, AbstractCatalogBrain):
            metadata = indexing.metadata_for_brain(obj)
        else:
            metadata = indexing.metadata_for_portal_content(obj, self.catalog)
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

        if hasattr(obj, 'getPath'):
            obj_dict['path'] = obj.getPath()
        else:
            obj_dict['path'] = '/'.join(obj.getPhysicalPath())
        return obj_dict

    @memoizedproperty
    def tasktracker_url(self): 
        # XXX todo all this logic prob ought be in oc-tt in a viewlet
        loc = getUtility(IProvideSiteConfig).get('tasktracker path')
        return "%s%s" % (self.context.absolute_url(), loc)
        
    @memoizedproperty
    def project_path(self):
        return '/'.join(self.context.getPhysicalPath())

    def _prep_editable_deletable(self, item, show_deletes=None):
        # Mark stuff that can't be edited or deleted.  This is another
        # speed hack to handle bugs 1330 (and 1158 via show_deletes())
        # but again, we don't check security on each object.
        if show_deletes is None:
            show_deletes = self.show_deletes()
        if item['id'] == PROJ_HOME:
            item['readonly'] = True
            item['nodelete'] = True
        if not show_deletes:
            item['nodelete'] = True
        return item

    def _sorted_items(self, item_type, sort_by=None, sort_order='ascending'):
        query = dict(portal_type=self._portal_type[item_type],
                     path=self.project_path,
                     sort_on=sort_by,
                     sort_order=sort_order)
        brains = self.catalog(**query)
        needed_values = self.needed_values[item_type]
        collection = ContentsCollection(item_type, self)
        show_deletes = self.show_deletes()
        for brain in brains:
            item = self._make_dict_and_translate(brain, needed_values)
            item = self._prep_editable_deletable(item)
            collection.append(item)
        return collection

    @memoizedproperty
    def pages(self):
        return self._sorted_items('pages', 'sortable_title')

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

    def _delete(self, brains, sources):
        """
        delete the objects named by the list of sources and referenced
        by the list of brains passed in.  returns ([deleted_ids],
        [failed_nondeleted_ids])

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
            if not brain.getPath() in sources:
                continue
            path = brain.getPath()
            parent_path, brain_id = path.rsplit('/', 1)
            parent_path = parent_path.split(self.project_path, 1)[-1].strip('/')
            parents.setdefault(parent_path, []).append((brain_id, path))
            
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
                paths = dict(child_ids)
                child_ids = [x[0] for x in child_ids]
                deletees = list(child_ids)
                try:
                    parent.manage_delObjects(child_ids)  ## dels ids from list as objs are deleted
                except (AttributeError, BadRequest):
                    # if deletion failed for a child, an error is raised and the
                    # child_ids will not be removed
                    pass
            if child_ids: # deletion failed for some objects
                surviving_objects.extend(paths[x] for x in child_ids)  ## what's left in 'child_ids' was not deleted
                deleted_objects.extend([paths[oid] for oid in deletees
                                        if oid not in child_ids]) ## the difference btn deletees and child_ids == deleted
            else: # deletion succeeded for every object
                deleted_objects.extend(paths[x] for x in deletees)
        
        # if any additional objects (ie file attachments) were deleted
        # as a consequence, add them to deleted_objects too
        if collateral_damage: 
            for oid in deleted_objects:
                extra = collateral_damage.get(oid)
                if extra: deleted_objects.extend(extra)

        return (deleted_objects, surviving_objects)

    @memoize
    def show_deletes(self):
        mtool = getToolByName(self.context, 'portal_membership')
        return mtool.checkPermission('Delete objects', self.context)

    def _resort(self, item_type, sort_by=None, sort_order=None):
        sort_by = self.needed_values[item_type].sortable(sort_by)
        new_objs = self._sorted_items(item_type, sort_by, sort_order)
        return new_objs

    @action('resort')
    def resort(self, sources, fields=None):
        item_type = self.request.form.get("item_type")
        if item_type not in self._portal_type:
            return False

        sort_by = self.request.form.get("sort_by")
        sort_order = self.request.form.get("sort_order", 'descending')
        items = self._resort(item_type, sort_by, sort_order)

        if sort_order == 'ascending':
            sort_order = 'descending'
        else:
            sort_order = 'ascending'

        thead_macro = self.template.macros['item_thead_snippet']
        thead_data = dict(item_type=item_type,
                          item_date_author_header=(item_type=='pages' and "Last Modified" or "Created"),
                          sort_on=sort_by,
                          sort_order=sort_order,
                          item_collection=items)
        thead_context = tal.create_tal_context(self, **thead_data)
        thead_obj = {'html': tal.render_tal(thead_macro, thead_context),
                     'effects': '',
                     'action': 'replace'
                     }

        tbody_macro = self.template.macros['item_tbody_snippet']
        tbody_data = dict(item_collection=items)
        tbody_context = tal.create_tal_context(self, **tbody_data)
        tbody_obj = {'html': tal.render_tal(tbody_macro, tbody_context, macros=self.template.macros),
                     'effects': 'highlight',
                     'action': 'replace'
                     }
        
        return {'oc-%s-tbody' % item_type: tbody_obj,
                'oc-%s-thead' % item_type: thead_obj
                }

    @action('delete')
    def delete_items(self, sources, fields=None):
        if self.request.environ['REQUEST_METHOD'] != 'POST':
            # Only non-javascript clients should see this.
            # Send them to a form they can POST from.
            # We can't just call & return the form; octopus hijacks the output.
            url = '%s/delete-form/?%s' % (self.context.absolute_url(),
                                          ZTUtils.make_query(sources=sources))
            self.request.response.redirect(url)
            return None
            
        item_type = self.request.form.get("item_type")

        if item_type == 'pages' and PROJ_HOME in sources:
            sources.remove("project-home")

        ids = [x.split("/")[-1] for x in sources]
        brains = self.catalog(id=ids, path=self.project_path)

        deletions, survivors = self._delete(brains, sources)
        # for now we'll only return the deleted obj ids. later we may return the survivors too.
        commands = {}
        for obj_id in deletions:
            commands[obj_id] = {
                'action': 'delete'
                }
        return commands

    def render_row(self):
        pass

    @action('update')
    def update_items(self, sources, fields=None):
        item_type = self.request.form.get("item_type")
        mtool = getToolByName(self.context, 'portal_membership')

        if item_type == 'pages' and PROJ_HOME in sources:
            sources.remove("project-home")

        ids = [x.split("/")[-1] for x in sources]
        brains = self.catalog(id=ids, path=self.project_path)

        snippets = {}
        objects = dict([(b.getPath(), b.getObject()) for b in brains])
        
        macro = self.template.macros['item_row']
        for old, new in zip(sources, fields):
            page = objects[old]
            if bool(mtool.checkPermission(ModifyPortalContent, page)):
                page.setTitle(new['title'])
                page.reindexObject(('Title',))

            data = dict(item=self._make_dict_and_translate(page, self.needed_values[item_type]),
                        item_type=item_type,
                        item_collection=dict(editable=self.needed_values[item_type].editable),
                        )
            
            tal_context = tal.create_tal_context(self, **data)
            path = '/'.join(page.getPhysicalPath())
            snippets[path] = {
                'html': tal.render_tal(macro, tal_context),
                'effects': 'highlight',
                'action': 'replace'
                }
        return snippets


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

    def append(self, item):
        list.append(self, item)

    def extend(self, items):
        list.extend(self, items)
