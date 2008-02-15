from Products.CMFCore.utils import getToolByName
from opencore.interfaces import IProject
from opencore.tasktracker.interfaces import ITaskTrackerFeatureletInstalled
from opencore.utility.interfaces import IHTTPClient
from opencore.utils import get_opencore_property
from plone.memoize.instance import memoizedproperty, memoize
from topp.featurelets.base import BaseFeaturelet
from topp.featurelets.interfaces import IFeaturelet
from zope.component import getUtility
from zope.interface import implements
import logging

log = logging.getLogger('opencore.tasktracker')


class TaskTrackerFeaturelet(BaseFeaturelet):
    # could we make featurlets named utilities?
    # currently featurelet all have the same state always
    """
    A featurelet that installs a Task Tracker
    """

    implements(IFeaturelet)

    id = "tasks"
    title = "Task Tracker"
    installed_marker = ITaskTrackerFeatureletInstalled

    _required_interfaces = BaseFeaturelet._required_interfaces + (IProject,)
    _info = {'menu_items': ({'title': u'Tasks',
                             'description': u'Task tracker',
                             'action': 'tasks'
                             },
                            ),
             }

    @property
    def uri(self):
        return get_opencore_property('tasktracker_uri')

    @property
    def active(self):
        return bool(self.uri)

    @property
    def init_uri(self):
        return "%s/project/initialize/" % self.uri

    # we're currently destroying projects, not uninitializing them
    @property
    def uninit_uri(self):
        return "%s/project/uninitialize/" % self.uri

    @property
    def destroy_uri(self):
        return "%s/project/destroy/" % self.uri

    @memoizedproperty
    def http(self):
        return getUtility(IHTTPClient)

    def _makeHttpReqAsUser(self, uri, obj, method="POST", headers=None):
        if headers is None: headers = {}
        auth = obj.acl_users.credentials_signed_cookie_auth

        user_id = getToolByName(obj, 'portal_membership').getAuthenticatedMember().getId()
        headers['Cookie'] = auth.generateCookie(user_id)
        headers['X-Openplans-Project'] = obj.getId()
        return self.http.request(uri, method=method, headers=headers)

    def deliverPackage(self, obj):
        if not self.active:
            # we don't have a TT URI set, don't do anything
            log.info('Failed to add TaskTracker featurelet: no TT URI set')
            return

        #XXX: we send both headers for now so that TT and OC can be updated
        #independently.  The first can be removed once TT is updated.
        header = {"X-Tasktracker-Initialize":"True"}
        header = {"X-Openplans-Tasktracker-Initialize":"True"}
        response, content = self._makeHttpReqAsUser(self.init_uri, obj=obj,
                                                    headers=header)

        if response.status != 200:
            raise AssertionError("Project initialization failed: status %d (maybe TaskTracker isn't running?)" % response.status)
        return BaseFeaturelet.deliverPackage(self, obj)

    def removePackage(self, obj, raise_error=True):
        # sending message to tasktracker happens through cabochonclient now
        return
