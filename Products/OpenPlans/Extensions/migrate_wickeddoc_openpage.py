from Acquisition import aq_base
from Products.ATContentTypes.migration.walker import CatalogWalker
from Products.ATContentTypes.migration.migrator import CMFItemMigrator
from Products.CMFCore.utils import getToolByName

class OpenPageMigrator(CMFItemMigrator):
    walker = CatalogWalker
    map = {'getRawText': 'setText'}

    src_portal_type = 'Document'
    src_meta_type = 'WickedDoc'
    dst_portal_type = 'OpenPage'
    dst_meta_type = 'OpenPage'

    def custom(self):
        self.new.setContentType(self.old.getContentType())

    def migrate_CMFEditionsAttributes(self):
        """
        Migrate CMFEditions specific attributes that may not exist.
        """
        if hasattr(aq_base(self.old), 'version_id'):
            self.new.version_id = self.old.version_id
        if hasattr(aq_base(self.old), 'location_id'):
            self.new.location_id = self.old.location_id

    def migrate_annotations(self):
        if hasattr(aq_base(self.old), '__annotations__'):
            self.new.__annotations__ = self.old.__annotations__

def migrate_wickeddoc_openpage(self):
    catalog = getToolByName(self, 'portal_catalog')
    portal = getToolByName(self, 'portal_url').getPortalObject()
    out = []

    migrator = OpenPageMigrator
    out.append('*** Migrating %s to %s ***\n' % (migrator.src_portal_type,
                                                 migrator.dst_portal_type))
    try:
        w = CatalogWalker(migrator, portal) # ATCT-0.2
    except AttributeError:
        w = CatalogWalker(portal, migrator) # ATCT-1.0
    w_result = w.go()
    if type(w_result) == type(''):
        out.append(w_result) # ATCT-0.2
    else:
        out.append('%s Migrated\n' % migrator.src_portal_type)

    wf = getToolByName(self, 'portal_workflow')
    count = wf.updateRoleMappings()
    out.append('Workflow: %d object(s) updated.' % count)

    catalog.refreshCatalog(clear=1)
    out.append('Portal catalog updated.')

    ttool = getToolByName(self, 'portal_types')
    doc_fti = ttool.getTypeInfo('Document')
    if doc_fti.Metatype() != 'OpenPage':
        atct_tool = getToolByName(self, 'portal_atct')
        if ttool.hasObject('WickedDoc'):
            ttool.manage_delObjects('WickedDoc')
        get_transaction().commit(1)
        atct_tool._changePortalTypeName('Document', 'WickedDoc',
                                        global_allow=0,
                                        title='WickedDoc')
        get_transaction().commit(1)
        atct_tool._changePortalTypeName('OpenPage', 'Document',
                                        global_allow=1,
                                        title='Page')
        out.append('Document types switched')

    return '\n'.join(out)
