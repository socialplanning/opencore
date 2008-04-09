import re

from opencore.project.browser.contents import ProjectContentsView
from opencore.project.utils import get_featurelets
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile


class LatestActivityView(ProjectContentsView):
    """
    displays latest activity for a project.
    This is a concept class (sandbox) for the time being
    I think/hope the appropriate architecture will
    emerge from playing with it
    """

    # XXX this is necessary because the ProjectContentsView stupidly overrides template

    # end-user views are really not intended to be extended. if a view has functionality you need,
    # that is probably a good indication that the functionality should be moved out of the view
    # altogether and into an object adapter, utility, or function ASAP -egj
    template = ZopeTwoPageTemplateFile('latest_activity.pt')    

    def __init__(self, context, request):                
        ProjectContentsView.__init__(self, context, request)

        # XXX this logic should live at a higher level
        # maybe project base view
        self.logo_url = context.getLogo()
        if self.logo_url:
            self.logo_url = self.logo_url.absolute_url()
        else:
            self.logo_url = self.defaultProjLogoThumbURL

    def team_manager(self):
        """
        returns whether the member has permission to manage the team
        """
        # XXX this method is deprecated
        return context.isProjectAdmin()
        mem_id = self.member_info.get('id')
        if mem_id is None:
            return False
        return mem_id in self.context.projectMemberIds(admin_only=True)

        
    ### methods to obtain feed snippets
    ### TODO: use viewlets

    def feed(self, path):
        snip = self.context.restrictedTraverse(path)
        return snip()        

    def blog_feed(self):
        if self.has_blog:
            return self.feed('blogfeed')
        return ''

    def wiki_feed(self):
        return self.feed('blank-slate-feed')

    def discussions_feed(self):
        if self.has_mailing_lists:
            return self.feed('lists/blank-slate-feed')
        return ''

    def team_feed(self):
        return self.feed('teamfeed')

