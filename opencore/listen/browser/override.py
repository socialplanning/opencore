from opencore.listen.browser.view import NuiMailingListView as BaseView
from Acquisition import aq_inner


class ArchiveWrapper(BaseView):
    """wraps archive's default view so it can be used as the index for
    the archive's container"""
        
    def get_forum_view(self):
        archive = aq_inner(self.context.archive)
        return archive.restrictedTraverse('forum_view')

    def index(self):
        pass

    def __call__(self):
        BaseView.__call__(self)
        forum_view = self.get_forum_view()
        return forum_view()
