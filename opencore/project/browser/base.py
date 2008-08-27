from Acquisition import aq_inner
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from opencore.browser.base import BaseView, view
from opencore.project import LATEST_ACTIVITY
from opencore.project import PROJ_HOME
from opencore.project.utils import get_featurelets
from plone.memoize.instance import memoizedproperty
from topp.featurelets.interfaces import IFeatureletSupporter, IFeaturelet
from topp.utils import text
from zope.component import queryAdapter


class ProjectBaseView(BaseView):

    # XXX to move to project

    @memoizedproperty
    def has_mailing_lists(self):
        from zope.component import ComponentLookupError
        try:
            from opencore.listen.interfaces import IListenContainer
            return IListenContainer(self.context)
        except ComponentLookupError:
            return False

    @memoizedproperty
    def has_task_tracker(self):
        return self._has_featurelet('tasks')

    @memoizedproperty
    def has_blog(self):
        return self._has_featurelet('blog')

    def _get_featurelet(self, flet_id):
        flets = get_featurelets(self.context)
        for flet in flets:
            if flet['name'] == flet_id:
                return flet
        return None

    def _has_featurelet(self, flet_id):
        flet_adapter = queryAdapter(
                         IFeatureletSupporter(self.context),
                         IFeaturelet,
                         name=flet_id)
        if flet_adapter is None:
            return False
        return flet_adapter.installed

    #@@ wiki should just be another featurelet
    @staticmethod
    def intrinsic_homepages():
        """return data for homepages intrinsic to opencore
        (not featurelet-dependent)
        """
        # XXX maybe this should just be a list?
        # @@ maybe this should just be an ini?
        return [
                 dict(id='latest-activity',
                      title='Summary',
                      url=LATEST_ACTIVITY,
                      checked=True,
                      ),

                 dict(id='wiki',
                      title='Pages',
                      url=PROJ_HOME,
                      checked=False,
                      ),
                 ]

    valid_id = staticmethod(text.valid_id)
    valid_title = staticmethod(text.valid_title)

    @view.mcproperty
    def project_info(self):
        """
        Returns a dict containing information about the
        currently-viewed project for easy template access.

        calculated once
        """

        from opencore.interfaces.workflow import IReadWorkflowPolicySupport
        proj_info = {}
        if self.piv.inProject:
            proj = aq_inner(self.piv.project)
            security = IReadWorkflowPolicySupport(proj).getCurrentPolicyId()

            proj_info.update(navname=proj.Title(),
                             fullname=proj.getFull_name(),
                             title=proj.Title(),
                             security=security,
                             url=proj.absolute_url(),
                             description=proj.Description(),
                             featurelets=self.piv.featurelets,
                             location=proj.getLocation(),
                             obj=proj)

        return proj_info

    def authenticator(self):
        return self.get_tool('browser_id_manager').getBrowserId(create=True)

    def authenticator_input(self):
        return '<input type="hidden" name="authenticator" value="%s" />' % self.authenticator()

