from opencore.listen.browser.view import ListenBaseView
from Acquisition import aq_inner


class ArchiveWrapper(ListenBaseView):
    """wraps archive's default view so it can be used as the index for
    the archive's container"""

    def __init__(self, context, request):
        self.context = context

    def get_forum_view(self):
        archive = aq_inner(self.context.archive)
        return archive.restrictedTraverse('forum_view')

    def __call__(self):
        forum_view = self.get_forum_view()
        return forum_view()
