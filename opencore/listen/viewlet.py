from opencore.listen.interfaces import IListenContainer, IListenFeatureletInstalled

from opencore.framework.editform import IEditForm
from opencore.framework.editform import EditFormViewlet

from zope.interface import implements
from zope.interface import Interface, alsoProvides, noLongerProvides
from zope.component import adapts

from OFS.interfaces import IObjectManager

class ListenInstallationViewlet(EditFormViewlet):

    title = "Mailing lists"
    sort_order = 50

    @property
    def enabled(self):
        return IListenFeatureletInstalled.providedBy(self.context)

    def enable(self, context):
        if self.enabled:
            return
        create_listen_container(context, 'lists')
        alsoProvides(context, IListenFeatureletInstalled)

    def disable(self, context):
        if not self.enabled:
            return
        remove_listen_container(context, 'lists')
        noLongerProvides(context, IListenFeatureletInstalled)

    def save(self, context, request):
        enable = request.form.get('listen', False)
        if enable:
            self.enable(context)
        else:
            self.disable(context)

    def render(self):
        from opencore.interfaces.adding import IAddProject
        if IAddProject.providedBy(self.context):
            return "<input type='hidden' name='listen' value='1' />"
        return "<input type='checkbox' name='listen'>Mailing Lists</input>"

from zope.component import adapter
from zope.interface import implementer

@adapter(IListenFeatureletInstalled)
@implementer(IListenContainer)
def get_listen_container(context):
    return context['lists']

def remove_listen_container(context, id):
    object_manager = IObjectManager(context)
    object_manager.manage_delObjects(ids=[id])

from Products.CMFCore.utils import getToolByName
from zope.event import notify
from opencore.feed.interfaces import ICanFeed
def create_listen_container(context, id):
    type_factory = getToolByName(context, 'portal_types')
    object_manager = IObjectManager(context)

    type_factory.constructContent('Folder', object_manager,
                                  id, title='Mailing lists')
    container = context._getOb('lists')

    # this next line sets the (default view) of the new Folder object
    # to the "mailing lists" layout, which is set up to render the
    # @@mailing_lists view, defined in opencore.listen.browser
    container.setLayout('mailing_lists')

    alsoProvides(container, IListenContainer)
    alsoProvides(container, ICanFeed) # ?~? seems like this could be global reg..?
    listen_featurelet_installed(context)

from opencore.listen.utils import getSuffix
from zope.component import getUtility
from Products.listen.interfaces import IListLookup
from opencore.listen.mailinglist import OpenMailingList
from zope.i18n import translate
from opencore.project.utils import project_noun
from opencore.i18n import _
from zope.app.event.objectevent import ObjectCreatedEvent
from Products.listen.interfaces import IWriteMembershipList
def listen_featurelet_installed(proj):
    """need to create a default discussion mailing list
       and subscribe all project members to the list"""
    proj_id = proj.getId()
    proj_title = proj.Title().decode('utf-8')
    ml_id = '%s-discussion' % proj_id
    address = '%s%s' % (ml_id, getSuffix())

    # need to verify that a mailing list with this name isn't already created
    portal = getToolByName(proj, 'portal_url').getPortalObject()
    ll = getUtility(IListLookup, context=portal)
    if ll.getListForAddress(address) is not None:
        # XXX we'll just silently fail for now, not sure what else we can do
        # psm maybe?
        return

    # XXX we need a request utility
    request = proj.REQUEST
    # invokeFactory depends on the title being set in the request
    ml_title = u'%s discussion' % (proj_title)
    request.set('title', ml_title)
    lists_folder = proj.lists.aq_inner
    lists_folder.invokeFactory(OpenMailingList.portal_type, ml_id)
    ml = lists_folder._getOb(ml_id)
    ml.mailto = ml_id
    ms_tool = getToolByName(proj, 'portal_membership')
    cur_mem_id = unicode(ms_tool.getAuthenticatedMember().getId())
    ml.managers = (cur_mem_id,)
    ml.setDescription(translate(_(u'discussion_list_desc', u'Discussion list for this ${project_noun}, consisting of all ${project_noun} members.',
                                  mapping={'project_noun':project_noun()}),
                                            context=request))
    notify(ObjectCreatedEvent(ml))

    memlist = IWriteMembershipList(ml)

    cat = getToolByName(portal, 'portal_catalog')
    teams = getToolByName(portal, 'portal_teams')
    try:
        team = teams._getOb(proj_id)
    except KeyError:
        # if the team doesn't exist
        # then nobody is on the project yet
        # so we only need to subscribe the current user
        memlist.subscribe(cur_mem_id)
        return
    active_states = teams.getDefaultActiveStates()
    team_path = '/'.join(team.getPhysicalPath())
    mships = cat(portal_type='OpenMembership', review_state=active_states, path=team_path)
    for mship in mships:
        memlist.subscribe(mship.getId)

from zope.interface import implementer
from zope.component import adapter
from opencore.frameworkk import IExtensibleContent
from opencore.project.browser.home_page import HomePageable, IHomePageable

@adapter(IExtensibleContent)
@implementer(IHomePageable)
def listen_home_page(context):
    container = IListenContainer(context)
    return HomePageable(container.getId(), container.Title(), container.absolute_url())
from zope.component import getGlobalSiteManager
gsm = getGlobalSiteManager()
gsm.registerSubscriptionAdapter(listen_home_page)
