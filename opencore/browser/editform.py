from Products.Five.viewlet.manager import ViewletManagerBase
from zope.component import getMultiAdapter
from zope.interface import implements
from zope.viewlet.interfaces import IViewletManager

def edit_form_manager(view, context=None):
    context = context or view.context
    manager = getMultiAdapter((context,
                               view.request,
                               view),
                              name='opencore.editform')
    assert IEditForm.providedBy(manager)
    return manager

from zope.interface import Interface
class IEditable(Interface):
    """
    Standard interface for editable content.

    Editform views, viewletmanagers, and viewlets should all conform
    to this interface.
    """

    def validate():
        """ 
        perform any necessary validation based on the current request
        by iterating through active viewlets.

        returns an error dictionary.
        """

    def save():
        """ save state based on the current request. """

class IEditForm(IViewletManager, IEditable):
    """ Viewlet manager for settings you can modify on a piece of content. """

class EditForm(ViewletManagerBase):
    implements(IEditForm)

    def validate(self):
        if not hasattr(self, 'viewlets'):
            # is this really necessary?
            self.update()

        errors = {}
        for viewlet in self.viewlets:
            errors.update(viewlet.validate(self.context, self.request))
        return errors

    def save(self):
        if not hasattr(self, 'viewlets'):
            # is this really necessary?
            self.update()

        for viewlet in self.viewlets:
            viewlet.save(self.context, self.request)

class EditFormViewlet(object):

    def validate(self, context, request):
        return {}

    def save(self, context, request):
        pass
