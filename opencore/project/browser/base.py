from Acquisition import aq_inner
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from opencore.browser.base import BaseView, view
from opencore.project import LATEST_ACTIVITY
from opencore.project import PROJ_HOME
from plone.memoize.instance import memoizedproperty
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
        return False

    @memoizedproperty
    def has_blog(self):
        return False

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

