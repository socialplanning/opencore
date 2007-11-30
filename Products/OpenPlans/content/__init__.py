import project
import team

from opencore.listen import mailinglist

z3ftis = (mailinglist.fti,)

# XXX: Monkeypatch wicked doc so that it supports undeletion.  This
# should use events, but IObjectWillBeRemovedEvents are not getting
# fired unless <five:containerEvents /> is enabled, in which case
# everything else breaks.
from wicked.atcontent.wickeddoc import WickedDoc
from Products.ATContentTypes.content.document import ATDocument
from Products.ploneundelete.interfaces import ICanBeUndeleted
from Products.ploneundelete.interfaces import IUndeleteSupport
from zope.component.exceptions import ComponentLookupError

def manage_beforeDelete(self, item, container):
    if ICanBeUndeleted.providedBy(item):
        try:
            undelete_container = IUndeleteSupport(container)
        except (ComponentLookupError, TypeError):
            undelete_container = None
        if undelete_container is not None:
            undelete_container.saveObjectInfo(item)
    ATDocument.manage_beforeDelete(self, item, container)

WickedDoc.manage_beforeDelete = manage_beforeDelete
