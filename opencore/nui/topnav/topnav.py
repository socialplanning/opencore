"""
TopNav view classes.
"""
from zope.component import getUtility

from plone.memoize import view

from Products.CMFCore.permissions import ModifyPortalContent
from Products.TeamSpace.permissions import ManageTeamMembership

from opencore.project.content import IProject

from opencore.nui.base import BaseView
from opencore.nui.contexthijack import HeaderHijackable
from opencore.nui.member.interfaces import ITransientMessage


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


class MemberMenuView(BaseView):
    """
    Contains the information req'd by the topnav's member context menu
    """
    @memoizedproperty
    def profile_url(self):
        return '%s/profile' % self.areaURL

    @memoizedproperty
    def profile_edit_url(self):
        return '%s/profile-edit' % self.areaURL

    @memoizedproperty
    def userprefs_url(self):
        return '%s/account' % self.areaURL

    @memoizedproperty
    def atMemberHome(self):
        result = False
        memfolder = self.miv.member_folder
        if memfolder is not None:
            homepage = memfolder._getOb(memfolder.getDefaultPage())
            if self.context == homepage and \
               self.request.ACTUAL_URL not in (self.userprefs_url,
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
             'selected': self.request.ACTUAL_URL in (self.profile_url, self.profile_edit_url),
             },
            )

        # only show "account" button if you're viewing yourself
        memfolder = self.miv.member_folder
        loggedinmember = self.loggedinmember
        if memfolder is not None and loggedinmember is not None:
            if self.miv.member_folder.getId() == self.loggedinmember.getId():
                menudata += (
                    {'content': 'Account',
                     'href': self.userprefs_url,
                     'selected': self.request.ACTUAL_URL == self.userprefs_url,
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
            proj_home = None
            dp = proj.getDefaultPage()
            if dp:
                proj_home = proj._getOb(dp)
            if self.context == proj_home:
                result = True
        return result

    @memoizedproperty
    def menudata(self):
        featurelets = self.piv.featurelets
        proj = self.piv.project
        proj_url = self.areaURL
        contents_url = "%s/contents" % proj_url
        team_url = "%s/team" % proj_url
        prefs_url = "%s/preferences" % proj_url
        manage_team_url = "%s/manage-team" % proj_url

        menudata = (
            {'content': 'Home',
             'href': proj_url,
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
                 'href': '%s/%s' % (proj_url,
                                    flet.get('url')),
                 'selected': self.is_flet_selected(flet)
                 },
                )

        menudata += (
            {'content': 'Team',
             'href': team_url,
             'selected': self.request.ACTUAL_URL == team_url,
             },
            )

        if self.membertool.checkPermission(ManageTeamMembership, proj):
            menudata += (
                {'content': 'Manage team',
                 'href': manage_team_url,
                 'selected': self.request.ACTUAL_URL == manage_team_url,
                 },

                {'content': 'Preferences',
                 'href': prefs_url,
                 'selected': self.request.ACTUAL_URL == prefs_url,
                 },
                )

        team = proj.getTeams()[0]
        filter_states = tuple(team.getActiveStates()) + ('pending',)
        if self.loggedin and self.member_info.get('id') not in \
               team.getMemberIdsByStates(filter_states):
            req_mship_url = '%s/request-membership' % proj.absolute_url()
            menudata += (
                {'content': 'Join project',
                 'href': req_mship_url,
                 'selected': self.request.ACTUAL_URL == req_mship_url,
                 },
                )

        return menudata


    def is_flet_selected(self, flet):
        flet = flet.get('title').lower()
        if flet == 'mailing lists':
            lists_url = '/'.join((self.areaURL, 'lists'))
            return self.request.ACTUAL_URL.startswith(lists_url)
        elif flet == 'tasks':
            header = self.request.get_header('X-Openplans-Application')
            return header == 'tasktracker'
        return False

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

            {'content': 'Join',
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
        tm = getUtility(ITransientMessage, context=self.portal)
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
