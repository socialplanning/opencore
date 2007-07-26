from cStringIO import StringIO

from zope.component import getUtility
from AccessControl.interfaces import IRoleManager

from Products.listen.interfaces import IListLookup
from Products.listen.lib.common import assign_local_role

OWNER_ROLE = 'Owner'

def migrate_listen_permissions(self):
    out = StringIO()

    ll = getUtility(IListLookup)
    out.write('obtained list lookup utility\n')

    for mapping in ll.showAddressMapping():
        path = mapping['path']
        try:
            ml = self.unrestrictedTraverse(path)
        except AttributeError:
            out.write("Mailing List '%s' not found\n" % path)
            continue
        managers = ml.managers
        list_role_manager = IRoleManager(ml)
        assign_local_role(OWNER_ROLE, managers, list_role_manager)
        out.write("Assigned local roles for list: '%s'\n" % ml.Title())

    return out.getvalue()
