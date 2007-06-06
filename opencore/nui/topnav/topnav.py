"""
TopNav view classes.
"""

from plone.memoize import view
memoizedproperty = lambda func: property(view.memoize(func))

from opencore.nui.base import BaseView as OpencoreView

class TopNavView(OpencoreView):
    """
    Provides req'd information for rendering top nav in any context.
    """
    @memoizedproperty
    def contextmenu(self):
        if self.piv.inProject:
            viewname = 'topnav-project-menu'
        elif self.inmember:
            viewname = 'topnav-member-menu'
        else:
            viewname = 'topnav-default-menu'
        return self.get_view(viewname)

    @memoizedproperty
    def usermenu(self):
        if self.loggedin:
            viewname = 'topnav-auth-user-menu'
        else:
            viewname = 'topnav-anon-user-menu'
        return self.get_view(viewname)
