from opencore.browser.topnav.topnav_menuitem import BaseFeatureletMenuItem
from opencore.tasktracker.interfaces import ITaskTrackerFeatureletInstalled

class TasktrackerMenuItem(BaseFeatureletMenuItem):
    name = u'Task tracker'
    supp_must_provide = ITaskTrackerFeatureletInstalled
    item_url = 'tasks'
