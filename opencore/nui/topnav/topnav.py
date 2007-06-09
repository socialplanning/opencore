"""
TopNav view classes.
"""

from plone.memoize import view
memoizedproperty = lambda func: property(view.memoize(func))

from Products.CMFCore.permissions import ModifyPortalContent

from opencore.nui.base import BaseView 


class TopNavView(BaseView):
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


class MemberMenuView(BaseView):
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


class ProjectMenuView(BaseView):
    """
    Contains the info req'd by the topnav's project context menu
    """
    @memoizedproperty
    def atProjectHome(self):
        result = False
        proj = self.piv.project
        if proj is not None:
            proj_home = proj._getOb(proj.getDefaultPage())
            if self.context == proj_home:
                result = True
        return result

    @memoizedproperty
    def menudata(self):
        featurelets = self.piv.featurelets
        contents_url = "%s/contents" % self.areaURL
        prefs_url = "%s/preferences" % self.areaURL

        menudata = (
            {'content': 'Home',
             'href': self.areaURL,
             'selected': self.atProjectHome,
             },

            {'content': 'Contents',
             'href': contents_url,
             'selected': self.request.ACTUAL_URL == contents_url,
             },
            )

        for flet in featurelets:
            menudata += (
                {'content': flet.get('title'),
                 'href': '%s/%s' % (self.areaURL,
                                    flet.get('url')),
                 'selected': False, # XXX <-- need to calculate
                 },
                )

        if self.membertool.checkPermission(ModifyPortalContent,
                                           self.piv.project):
            menudata += (
                {'content': 'Preferences',
                 'href': prefs_url,
                 'selected': self.request.ACTUAL_URL == prefs_url,
                 },
                )

        return menudata


class AnonMenuView(BaseView):
    """
    View class for the user menu when user is anonymous.
    """
    @memoizedproperty
    def menudata(self):
        menudata = (

            {'content': 'Log In',
             'href': '%s/login' % self.siteURL,
             },

            {'content': 'Join',
             'href': '%s/join' % self.siteURL,
             },

            {'content': 'Help',
             'href': '%s/help' % self.siteURL,
             },

            )

        return menudata


class AuthMenuView(BaseView):
    """
    View class for the user menu when user is logged in.
    """
    @memoizedproperty
    def menudata(self):
        mem_data = self.mem_data_map
        
        menudata = (

            {'content': "%s's Stuff" % mem_data.get('id'),
             'href': mem_data.get('url'),
             },

            {'content': 'Log Out',
             'href': '%s/logout' % self.siteURL,
             },

            {'content': 'Help',
             'href': '%s/help' % self.siteURL,
             },

            )

        return menudata
