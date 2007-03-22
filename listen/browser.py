from AccessControl import Unauthorized

from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import normalizeString
from Products.plone_schemas.plone_views import AddView as BaseAddView

class ListAddView(BaseAddView):
    """
    Override 'add' function b/c it was causing recursion errors.
    """
    def add(self, content):
        context = self.context
        ttool = getToolByName(context, 'portal_types', None)
        pt = getattr(content, 'portal_type', '')
        fti = getattr(ttool, pt, None)
        context_fti = None
        if ttool is not None:
            context_fti = ttool.getTypeInfo(context)
        if fti is not None and context_fti is not None:
            if not context_fti.allowType(pt):
                raise ValueError, 'Disallowed subobject type: %s'%pt
            if not fti.isConstructionAllowed(context):
                raise Unauthorized, 'Object construction not allowed'

        title = self.request.form.get('field.title')
        list_id = normalizeString(title, context)
        content._setId(list_id)
        context._setOb(list_id, content)
        return context._getOb(list_id)

