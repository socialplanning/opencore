from opencore.nui.project.view import ProjectBaseView

class RecentUpdatesView(ProjectBaseView):
    """
    things we need:
    first:
    recent wikipage updates (just query catalog sorted on last_modified? check rollie's wireframes to see if multiple updates per page show up, in which case this is harder)
    listen threads with recent messages (same as above)
    then: recent blog posts (pull wordpress rss feed -- use some sort of utility/tool [what is the difference?] in opencore.wordpress?)
    then: tasktracker .. maybe.
    """
