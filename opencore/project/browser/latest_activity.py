from opencore.project.browser.base import ProjectBaseView

class LatestActivityView(ProjectBaseView):
    """
    displays latest activity for a project.
    This is a concept class (sandbox) for the time being
    I think/hope the appropriate architecture will
    emerge from playing with it
    """

    def logo_url(self):
        logo = self.context.getLogo()
        if logo:
            return logo.absolute_url()
        else:
            return self.defaultProjLogoThumbURL

    def team_manager(self):
        """
        returns whether the member has permission to manage the team
        """
        # XXX this method is deprecated
        # should be replaced with below v
        return self.context.isProjectAdmin()
        
    ### methods to obtain feed snippets
    ### TODO: use viewlets

    def feed(self, path):
        snip = self.context.restrictedTraverse(path)
        return snip()        

    def wiki_feed(self):
        return self.feed('blank-slate-feed')

    def discussions_feed(self):
        if self.has_mailing_lists:
            return self.feed('lists/blank-slate-feed')
        return ''

    def team_feed(self):
        return self.feed('teamfeed')


    
