from decorator import decorator

from zope.component import getUtility
from zope.app.event.objectevent import ObjectCreatedEvent
from zope.event import notify

from Products.CMFCore.utils import getToolByName
from Products.listen.interfaces import IWriteMembershipList
from Products.listen.interfaces import IListLookup
from Products.listen.interfaces import IBecameASubscriber
from Products.QueueCatalog.QueueCatalog import CHANGED
from opencore.i18n import _
from opencore.listen.interfaces import ISyncWithProjectMembership, IListenFeatureletInstalled
from opencore.listen.mailinglist import OpenMailingList
from opencore.project.utils import get_featurelets
from utils import getSuffix
from opencore.project.utils import project_noun 
from zope.i18n import translate

def reindex_catalog(event):
    """
    When a list adds or removes a subscriber, we want to reindex
    that list's `mailing_list_subscribers` KeywordIndex in portal_catalog
    """
    email = event.email
    context = event.context
    context.reindexObject(idxs=['mailing_list_subscribers'])

def queue_member_lists_reindex(event):
    member = event.context
    old_email = event.old_email
    catalog = getToolByName(member, "portal_catalog")
    catalog_queue = getToolByName(member, "portal_catalog_queue")
    lists = catalog(mailing_list_subscribers=old_email)
    for brain in lists:
        # If we wanted to do it immediately, we'd say:
        # brain.getObject().reindexObject('mailing_list_subscribers')
        # But instead, we'll add it to the QueueCatalog
        path = brain.getPath()
        catalog_queue._update(path, CHANGED)

# make sure that modification date gets updated
# when new messages are sent to list
def mailinglist_msg_delivered(ml, event):
    ml.setModificationDate()

#XXX this is directly copied from the wordpress event code to check
# need to extract a method, or utility, or something
@decorator
def is_listen_featurelet_installed(f, mship_obj, action):
    team = mship_obj.aq_inner.aq_parent
    proj_id = team.getId()
    portal = getToolByName(mship_obj, 'portal_url').getPortalObject()
    try:
        project = portal.projects[proj_id]
    except KeyError:
        # cannot find project with same name as team (unit test only?)
        return
    for flet in get_featurelets(project):
        if flet['name'] == 'listen':
            break
    else:
        # no mailing lists on project
        return
    f(mship_obj, action)


@is_listen_featurelet_installed
def add_or_remove_membership(mship, remove=False):

    mem_id = mship.getId()
    team = mship.aq_inner.aq_parent
    proj_id = team.getId()
    portal = getToolByName(mship, 'portal_url').getPortalObject()
    listencontainer = portal.projects[proj_id].lists

    mlists = []

    for mlist in listencontainer.objectValues(spec='OpenMailingList'):
        if ISyncWithProjectMembership.providedBy(mlist):
            mlists.append(mlist)
           
    if not mlists:
        # no autosync mailing lists; silently fail
        return

    for ml in mlists:
        memlist = IWriteMembershipList(ml)

        if remove:
            memlist.unsubscribe(mem_id)
        else:
            memlist.subscribe(mem_id)

def add_membership(mship):
    return add_or_remove_membership(mship, remove=False)

def remove_membership(mship):
    return add_or_remove_membership(mship, remove=True)

def member_joined_project(mship, event):
    add_membership(mship)

def member_left_project(mship, event):
    remove_membership(mship)

def listen_featurelet_installed(proj, event):
    """need to create a default discussion mailing list
       and subscribe all project members to the list"""

    if proj.REQUEST.form.get("featurelet_skip_content_init", ""):
        return

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
    ml = lists_folder[ml_id]
    ml.mailto = ml_id
    ms_tool = getToolByName(proj, 'portal_membership')
    cur_mem_id = unicode(ms_tool.getAuthenticatedMember().getId())
    ml.managers = (cur_mem_id,)
    ml.setDescription(translate(_(u'discussion_list_desc',
                                  u'Discussion list for this ${project_noun}, consisting of all ${project_noun} members.',
                                  mapping={'project_noun':project_noun()}),
                                            context=request))


    # http://www.openplans.org/projects/opencore/lists/opencore-dev/archive/2009/04/1239543233615/forum_view
    from zope.interface import alsoProvides
    alsoProvides(ml, ISyncWithProjectMembership)

    notify(ObjectCreatedEvent(ml))

    memlist = IWriteMembershipList(ml)

    cat = getToolByName(portal, 'portal_catalog')
    teams = getToolByName(portal, 'portal_teams')
    try:
        team = teams[proj_id]
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
