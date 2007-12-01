"""
TopNav view classes.
"""
from Products.CMFCore.permissions import ModifyPortalContent
from Products.TeamSpace.permissions import ManageTeamMembership
from opencore.browser.base import BaseView
from opencore.interfaces.message import ITransientMessage
from opencore.nui.contexthijack import HeaderHijackable
from opencore.project.content import IProject
from opencore.project import PROJ_HOME
from opencore.content.page import OpenPage
from operator import itemgetter
from plone.memoize import view


memoizedproperty = lambda func: property(view.memoize(func))


class TopNavView(HeaderHijackable):
    """
    Provides req'd information for rendering top nav in any context.
    """
    @memoizedproperty
    def contextmenu(self):
        if self.inmember:
            viewname = 'topnav-member-menu'
        elif self.inproject:
            viewname = 'topnav-project-menu'
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

    def siteroot_link(self, urn, name):
        here = self.request.ACTUAL_URL.split('/')[-1]
        selected = urn.split('/')[-1] == here
        css = selected and ' class="oc-topnav-selected"' or ''
        urn = '/'.join((self.siteURL, urn))
        return '<li%s><a href="%s">%s</a></li>' % (css, urn, name)

class AnonMenuView(BaseView):
    """
    View class for the user menu when user is anonymous.
    """
    @memoizedproperty
    def menudata(self):
        menudata = (

            {'content': 'Sign in',
             'href': '%s/login' % self.siteURL,
             },

            {'content': 'Create account',
             'href': '%s/join' % self.siteURL,
             },

            )

        return menudata


class AuthMenuView(BaseView):
    """
    View class for the user menu when user is logged in.
    """
    @memoizedproperty
    def user_message_count(self):
        """
        returns the number of transient messages currently stored
        for the logged in member
        """
        tm = ITransientMessage(self.portal)
        msgs = tm.get_all_msgs(self.loggedinmember.getId())
        return len(msgs)

    @memoizedproperty
    def menudata(self):
        mem_data = self.member_info
        
        menudata = (

            {'content': 'Sign out',
             'href': '%s/logout' % self.siteURL,
             },

            )

        return menudata
