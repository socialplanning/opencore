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


class MemberMenuView(OpencoreView):
    """
    Contains the information req'd by the topnav's member context menu
    """
    @memoizedproperty
    def profile_url(self):
        return '%s/profile' % self.areaURL

    @memoizedproperty
    def contact_url(self):
        return '%s/contact' % self.areaURL

    @memoizedproperty
    def atMemberHome(self):
        result = False
        memfolder = self.miv.member_folder
        if memfolder is not None:
            homepage = memfolder._getOb(memfolder.getDefaultPage())
            if self.context == homepage and \
               self.request.ACTUAL_URL not in (self.contact_url,
                                               self.profile_url):
                result = True
        return result

    @memoizedproperty
    def menudata(self):
        menudata = (
            {'content': 'Home',
             'href': self.areaURL,
             'selected': self.atMemberHome,
             },

            {'content': 'Profile',
             'href': self.profile_url,
             'selected': self.request.ACTUAL_URL == self.profile_url,
             },

            {'content': 'Contact',
             'href': self.contact_url,
             'selected': self.request.ACTUAL_URL == self.contact_url,
             },
            )

        return menudata
