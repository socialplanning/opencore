from opencore.browser.base import BaseView, _
from opencore.project.utils import get_featurelets
from plone.memoize.instance import memoize, memoizedproperty
from topp.featurelets.interfaces import IFeatureletSupporter, IFeaturelet
from zope.component import queryAdapter
from opencore.project import LATEST_ACTIVITY
from opencore.project import PROJ_HOME
from topp.utils import text


class ProjectBaseView(BaseView):

    @memoizedproperty
    def has_mailing_lists(self):
        return self._has_featurelet('listen')

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
        return [ dict(id='wiki',
                      title='Pages',
                      url=PROJ_HOME,
                      checked=False,
                      ),
                 
                 dict(id='latest-activity',
                      title='Summary',
                      url=LATEST_ACTIVITY,
                      checked=True,
                      )
                 ]

    valid_id = staticmethod(text.valid_id)
    valid_title = staticmethod(text.valid_title)
