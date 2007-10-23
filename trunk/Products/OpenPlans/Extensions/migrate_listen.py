from Products.CMFCore.utils import getToolByName
from cStringIO import StringIO

from Products.OpenPlans.Extensions.Install import installZ3Types
from Products.OpenPlans.Extensions.setup import migrate_listen_member_lookup
from Products.OpenPlans.Extensions.setup import reinstallSubskins

def migrate_listen(self):
    out = StringIO()

    # set listen to the active property configuration
    portal_setup_tool = getToolByName(self, 'portal_setup')
    portal_setup_tool.setImportContext('profile-listen:default')
    out.write('updated generic setup tool properties\n')

    # run the listen import step
    portal_setup_tool.runImportStep('listen-various', True)
    out.write('Listen import step run\n')

    # remove the open mailing list fti
    portal_types = getToolByName(self, 'portal_types')
    portal_types.manage_delObjects(['Open Mailing List'])
    out.write('open mailing list fti removed\n')

    # now run the install z3types to add it back
    installZ3Types(self, out)
    out.write('z3 types installed (Open Mailing List fti)\n')

    # migrate the listen local utility
    # self, self?
    migrate_listen_member_lookup(self, self)
    out.write('listen member lookup utility migrated\n')

    # remove openplans skins
    portal_skins = getToolByName(self, 'portal_skins')
    skins_to_remove = ['openplans', 'openplans_images', 'openplans_patches', 'openplans_richwidget', 'openplans_styles']
    portal_skins.manage_delObjects(skins_to_remove)
    out.write('removed openplans skins: %s\n' % ', '.join(skins_to_remove))

    # reinstall openplans skins
    portal_quickinstaller = getToolByName(self, 'portal_quickinstaller')
    portal_quickinstaller.reinstallProducts(['opencore.siteui'])
    out.write('reinstall opencore.siteui - openplans skins\n')

    # reinstall subskins
    reinstallSubskins(self, self)
    out.write('subskins reinstalled\n')

    # run listen migration?

    return out.getvalue()
