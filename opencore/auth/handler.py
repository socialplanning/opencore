from urllib import urlencode
from lxml import etree

from DateTime import DateTime

from zope.event import notify
from zope.component import getUtility
from zope.app.event.objectevent import ObjectCreatedEvent

from Products.CMFCore.utils import getToolByName

from opencore.utility.interfaces import IHTTPClient


def copy_remote_member(event):
    """
    Creates a new member object that is a copy of one on the remote
    server.
    """
    h = getUtility(IHTTPClient)
    query = urlencode({'__ac_name': event.username,
                       '__ac_password': event.password,
                       }
                      )
    memurl = '%s/people/%s/memberinfo.xml?%s' % (event.siteurl, event.username,
                                                 query)
    resp, content = h.request(memurl, 'GET')
    member = etree.fromstring(content)
    newdata = {}
    for child in member.iterchildren():
        newdata[child.tag] = child.text
    newdata['password'] = event.password

    mdc = getToolByName(event.context, 'portal_memberdata')
    pf = mdc.portal_factory
    id_ = event.context.generateUniqueId('OpenMember')
    mem_folder = pf._getTempFolder('OpenMember')
    mem = mem_folder.restrictedTraverse('%s' % id_)
    mem = pf.doCreate(mem, event.username)
    mem.processForm(values=newdata)

    # force the member into an active state
    mem_wf = 'openplans_member_workflow'
    wfhist = mem.workflow_history.get(mem_wf)
    status = {'action': 'register_public',
              'review_state': 'public',
              'comments': '',
              'actor': event.username,
              'time': DateTime(),
              }
    wfhist += (status,)
    mem.workflow_history[mem_wf] = wfhist
    notify(ObjectCreatedEvent(mem))
