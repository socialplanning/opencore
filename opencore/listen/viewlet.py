from opencore.listen.interface import IListenContainer, IListenFeatureletInstalled

from opencore.framework.editform import IEditForm
from opencore.framework.editform import EditFormViewlet

from zope.interface import implements
from zope.interface import Interface, alsoProvides, noLongerProvides
from zope.component import adapts


class ListenInstallationViewlet(EditFormViewlet):

    title = "Mailing lists"
    sort_order = 50

    @property
    def enabled(self):
        return IListenFeatureletInstalled.providedBy(self.context)

    def enable(self, context):
        if self.enabled:
            return
        alsoProvides(context, IListenFeatureletInstalled)

    def disable(self, context):
        if not self.enabled:
            return
        noLongerProvides(context, IListenFeatureletInstalled)

    def save(self, context, request):
        enable = request.form.get('listen', False)
        if enable:
            self.enable(context)
        else:
            self.disable(context)

    def render(self):
        return "<input type='checkbox'>Mailing Lists</input>"

@adapter(IListenFeatureletInstalled)
@implementer(IListenContainer)
def get_listen_container(context):
    try:
        return context['lists']
    except AttributeError:
        create_listen_container(context, 'lists')
        return context._getOb('lists')

from Products.CMFCore.utils import getToolByName
from OFS.interfaces import IObjectManager
from zope.event import notify
def create_listen_container(context, id):
    type_factory = getToolByName(context, 'portal_types')
    object_manager = IObjectManager(context)

    type_factory.constructContent('Folder', object_manager,
                                  id, 'Mailing lists')
    container = context._getOb('lists')
    container.setLayout('mailing_lists')
    alsoProvides(container, IListenContainer)
    alsoProvides(container, ICanFeed) # ?~?
    # notify(ListenFeatureletCreatedEvent(obj))
