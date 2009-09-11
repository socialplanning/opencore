from opencore.project.browser.base import ProjectBaseView

from opencore.listen.interfaces import ISyncWithProjectMembership
from opencore.listen.interfaces import IListenFeatureletInstalled
from opencore.listen.interfaces import IListenContainer
from opencore.listen.interfaces import IOpenMailingList

def find_membership_synced_lists(context):
    project = IListenFeatureletInstalled(context)
    lists_folder = IListenContainer(project.lists)

    membership_synced_lists = []
    for item in lists_folder.values():
        try:
            membership_synced_lists.append(
                ISyncWithProjectMembership(IOpenMailingList(item))
                )
        except TypeError:
            continue
    return membership_synced_lists

from opencore.i18n import _
class ContactTeamView(ProjectBaseView):
    def __call__(self, *args, **kw):
        lists = find_membership_synced_lists(self.context)

        if len(lists) == 1:
            list = lists[0]
            return self.redirect('%s/archive/new_topic' % list.absolute_url())

        if len(lists) > 1:
            # XXX todo this should really display a "post new message" form
            #     with some sort of dropdown of possible lists to send the
            #     message to (suggestion by pierre)
            list = lists[0]
            return self.redirect('%s/archive/new_topic' % list.absolute_url())

        if len(lists) == 0:
            self.add_status_message(_(u'no_membership_synced_lists',
                                      "Sorry, you can't do this! Please <a href='/contact-site-admin'>contact a site administrator</a> and let them know what happened."))
            return self.redirect('.')
