from zope.component import adapter
from zope.app.event.interfaces import IObjectModifiedEvent
from zope.app.container.interfaces import IObjectAddedEvent, IContainerModifiedEvent
from zope.component import getUtility
from Products.CMFCore.utils import getToolByName

from Products.remember.interfaces import IReMember
from opencore.cabochon.interfaces import ICabochonClient

from cabochonclient import datetime_to_string
from datetime import datetime

from opencore.interfaces import IProject, IOpenPage
def _get_project(page):
    if IProject.providedBy(page):
        return page
    else:
        parent = getattr(page, 'aq_parent', None)
        if parent:
            return _get_project(parent)
        else:
            return None

def  _memhome_url(member):
    mtool = getToolByName(member, 'portal_membership')
    folder = mtool.getHomeFolder(member.getId())
    return '%s/%s' % (folder.absolute_url(),
                      folder.getDefaultPage())   

def _send_object_message(queue, page):
    if IOpenPage.providedBy(page):
        page_url = page.absolute_url()
        project = _get_project(page)
    elif IReMember.providedBy(page):
        page_url = _memhome_url(page)
        project = None
    else:
        return
    
    mtool = getToolByName(page, 'portal_membership')
    mem = mtool.getAuthenticatedMember()
    user = mem.id

    params = dict(url=page_url,
                  user=user,
                  date=datetime_to_string(datetime.now()))
    if project:
        params['categories'] = ['projects/' + project.id, 'openpage']

    queue.send_message(params)

@adapter(IObjectAddedEvent)
def objectAdded(event):
    cabochonclient = getUtility(ICabochonClient)
    queue = cabochonclient.queue("create_page")
    page = event.object
    _send_object_message(queue, page)

@adapter(IObjectModifiedEvent)
def objectModified(event):
    if IContainerModifiedEvent.providedBy(event):
        print "container modified"
        return
    cabochonclient = getUtility(ICabochonClient)    
    queue = cabochonclient.queue("edit_page")
    page = event.object
    _send_object_message(queue, page)
        
