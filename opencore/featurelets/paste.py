"""
Implements a base class for featurelets for PasteDeploy-accessible
WSGI apps.

The basic pattern for using this is::

    from zope.interface import implements, Interface
    from topp.featurelets.interfaces import IFeaturelet
    from opencore.featurelets.paste import BasePasteFeaturelet
    from myinterfaces import IMyFeatureletInstalled, IMyContainer

    class MyFeaturelet(BasePasteFeaturelet):

        implements(IFeaturelet)

        id = 'my_featurelet'
        title = 'My Featurelet'
        installed_marker = IMyFeatureletInstalled
        container_interface = IMyContainer
        _info = {'menu_items': ({'title': u'My Featurelet',
                                 'description': 'My feature Described',
                                 'action': id,
                                 },
                                )}

        # Distribution name:
        dist = 'MyFeature' 
        # paste.app_factory entry point name:
        ep_name = 'main' 
        # any keyword arguments that go to create the app; also you
        # can override entry_point_config:
        ep_kw = {} 

Be sure to then call ``MyFeaturelet.register()`` somewhere in your
startup code so that the featurelet gets registered with the system.
You can pass keyword arguments to register to customize the installation
locally.

"""

from OFS.interfaces import IObjectManager
from zope.interface import directlyProvides, implements, Interface
from topp.featurelets.base import BaseFeaturelet
from topp.zwsgi.zpaste import FivePasteWSGIAppBase
from Products.OpenPlans import utils
from Products.CMFCore.utils import getToolByName 

class ToppWSGIAppBase(FivePasteWSGIAppBase):

    def _get_app(self):
        app = FivePasteWSGIAppBase._get_app(self)
        app = ToppMiddleware(app)
        return app

class ToppMiddleware(object):

    """
    Middleware that adds TOPP-specific keys to the WSGI environment
    """

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        request = environ['zope.request']
        context = environ['zope.context']
        project = utils.get_project(context)
        environ['topp.project_name'] = project.getId()
        environ['topp.project_info'] = make_dict_from_project(project)
        pm = getToolByName(context, 'portal_membership')
        # Should we handled pm.isAnonymousUser() specially?
        member = pm.getAuthenticatedMember()
        print 'got member', repr(member)
        if not pm.isAnonymousUser():
            environ['topp.user_info'] = make_dict_from_member(member, project)
        environ['topp.project_members'] = ProjectMembers(project)
        # @@ This should probably be handled specially
        environ['paste.throw_errors'] = True
        return self.app(environ, start_response)

def make_dict_from_member(member, project):
    return {
        'username': member.getId(),
        'fullname': member.getFullname(),
        'email': member.getEmail(),
        'roles': member.getRolesInContext(project),
        'zope_member_object': member,
        }    

def make_dict_from_project(project):
    return {
        'name': project.getId(),
        'title': project.Title(),
        'zope_project_object': project,
        }

class ProjectMembers(object):
    
    def __init__(self, project):
        self.project = project

    def project_members(self):
        user_infos = []
        for member in self.project.projectMembers():
            user_infos.append(make_dict_from_member(member, self.project))
        return user_infos

    def __repr__(self):
        return '<Project member getter for project %r>' % self.project

class BasePasteFeaturelet(BaseFeaturelet):

    def __init__(self, **extra_config):
        self.extra_config = extra_config
        BaseFeaturelet.__init__(self)

    def entry_point_config(self, obj):
        """
        Override this to determine the keyword arguments to
        instantiate the WSGI app dynamically.
        """
        kwargs = self.ep_kw.copy()
        kwargs.update(self.extra_config)
        return kwargs

    def deliverPackage(self, obj):
        """
        See IFeaturelet
        """
        BaseFeaturelet.deliverPackage(self, obj)
        objmgr = IObjectManager(obj)
        kwargs = self.entry_point_config(obj)
        bucket = ToppWSGIAppBase(
            self.id, self.dist, self.ep_name,
            **kwargs)
        objmgr._setObject(self.id, bucket)
        directlyProvides(bucket, self.container_interface)
        return self._info

    def removePackage(self, obj):
        """
        See IFeaturelet
        """
        BaseFeaturelet.removePackage(self, obj)

        objmgr = IObjectManager(obj)
        objmgr.manage_delObjects(ids=[self.id])

    def register(cls, **extra_config):
        """
        Registers this class as a featurelet provider.  Any keyword
        arguments will turn into extra config for the WSGI application.
        """
        from zope.component import getUtility
        from topp.featurelets.interfaces import IFeatureletRegistry
        flet_registry = getUtility(IFeatureletRegistry)
        flet_registry.registerFeaturelet(cls(**extra_config))

    register = classmethod(register)
    
