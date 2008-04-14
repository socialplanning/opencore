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
        return self.context.isProjectAdmin()
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

    def is_project_member(self, id=None):
        """
        doess the currently authenticated member belong to the project?
        """
        if id is None:
            id = self.member_info.get('id')
        
        # if somebody calls this function in a template without first checking
        # if we're in a project, then we get a failure if we don't check if
        # the project is None
        proj = self.piv.project
        if proj is None:
            return False
        team = proj.getTeams()[0]
        filter_states = tuple(team.getActiveStates()) + ('pending',)
        return id in team.getMemberIdsByStates(filter_states)


