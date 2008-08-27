from decorator import decorator

from zope.component import getUtility
from zope.app.event.objectevent import ObjectCreatedEvent
from zope.event import notify

from Products.CMFCore.utils import getToolByName
from Products.listen.interfaces import IWriteMembershipList
from Products.listen.interfaces import IListLookup
from opencore.i18n import _
from opencore.listen.mailinglist import OpenMailingList
from opencore.project.utils import get_featurelets
from utils import getSuffix
from opencore.project.utils import project_noun 
from zope.i18n import translate

# make sure that modification date gets updated
# when new messages are sent to list
def mailinglist_msg_delivered(ml, event):
    ml.setModificationDate()

from opencore.listen.interfaces import IListenFeatureletInstalled

def project_for_membership(mship):
    """
    This should really be IOpenProject(mship)...?
    """
    team = mship.aq_inner.aq_parent
    proj_id = team.getId()
    portal = getToolByName(mship, 'portal_url').getPortalObject()
    return portal.projects[proj_id]

def member_joined_project(mship, event):
    project = project_for_membership(mship)
    default_list_name = '%s-discussion' % project.getId()
    # \  / or just try: IListenContainer(project)[default_list_name]
    #  \/  ... which could be formalized to IListenContainer(project).default_list
    #      ..... so this whole function could look like:
    #      .....  IWriteMembershipList(IListenContainer(IOpenProject(mship)).default_list).subscribe(IOpenMember(mship))
    #      ..... if we really wanted it to
    if IListenFeatureletInstalled.providedBy(project):
        try:
            ml = project['lists'][default_list_name]
        except AttributeError:
            return
        memlist = IWriteMembershipList(ml)
        memlist.subscribe(mship.getId())

def member_left_project(mship, event):
    project = project_for_membership(mship)
    default_list_name = '%s-discussion' % project.getId()
    if IListenFeatureletInstalled.providedBy(project):
        try:
            ml = project['lists'][default_list_name]
        except AttributeError:
            return
        memlist = IWriteMembershipList(ml)
        memlist.unsubscribe(mship.getId())

