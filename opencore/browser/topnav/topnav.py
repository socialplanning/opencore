"""
TopNav view classes.
"""
from Products.CMFCore.permissions import ModifyPortalContent
from Products.TeamSpace.permissions import ManageTeamMembership
from opencore.browser.base import BaseView
from opencore.browser.topnav.interfaces import ITopnavMenuItems
from opencore.interfaces.message import ITransientMessage
from opencore.nui.contexthijack import HeaderHijackable
from opencore.project.content import IProject
from opencore.content.page import OpenPage
from operator import itemgetter
from plone.memoize import instance
from plone.memoize import view
from zope.component import getMultiAdapter

memoizedproperty = lambda func: property(view.memoize(func))


class BaseMenuView(BaseView):

    @instance.memoizedproperty
    def areaURL(self):
        return self.area.absolute_url()


class TopNavView(HeaderHijackable, BaseMenuView):
    """
    Provides req'd information for rendering top nav in any context.
    """
    @memoizedproperty
    def contextmenu(self):
        """ask a viewlet manager for the context menu
           HeaderHijackable takes care of making sure that the context
           is set correctly if we are getting a request with certain
           headers set to specify the context"""
        manager = getMultiAdapter(
            (self.context, self.request, self),
            ITopnavMenuItems,
            name="opencore.topnavmenu")
        manager.update()
        return manager.render()

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



class MemberMenuView(BaseMenuView):
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
    def atMemberWiki(self):
        memfolder = self.miv.member_folder
        memfolder_url = memfolder.absolute_url()
        return memfolder_url in self.request.ACTUAL_URL and isinstance(self.context, OpenPage)

    @memoizedproperty
    def menudata(self):
        menudata = (
            {'content': 'Wiki',
             'href': self.areaURL,
             'selected': self.atMemberWiki,
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


class ProjectMenuView(BaseMenuView):
    """
    Contains the info req'd by the topnav's project context menu
    """

    def atProjectWiki(self):
        return self.request.ACTUAL_URL.startswith(self.areaURL) and \
               isinstance(self.context, OpenPage)

    @memoizedproperty
    def menudata(self):
        featurelets = self.piv.featurelets
        proj = self.piv.project
        proj_url = self.areaURL
        wiki_url = '%s/project-home' % (proj_url)
        contents_url = "%s/contents" % proj_url
        team_url = "%s/team" % proj_url
        prefs_url = "%s/preferences" % proj_url
        manage_team_url = "%s/manage-team" % proj_url
        can_manage = self.membertool.checkPermission(ManageTeamMembership,
                                                     proj)
        menudata = (
            {'content': 'Wiki',
             'href': wiki_url,
             'selected': self.atProjectWiki(),
             },
            )

        featurelets.sort(key=itemgetter('title'))
        for flet in featurelets:
            menudata += (
                {'content': flet.get('title'),
                 'href': '%s/%s' % (proj_url,
                                    flet.get('url')),
                 'selected': self.is_flet_selected(flet)
                 },
                )
        if can_manage:
            menudata += (
                {'content': 'Team',
                 'href': manage_team_url,
                 'selected': self.request.ACTUAL_URL == manage_team_url or
                 self.request.ACTUAL_URL == team_url,
                 },
                )
        else:
            menudata += (
                {'content': 'Team',
                 'href': team_url,
                 'selected': self.request.ACTUAL_URL == team_url,
                 },
                )

            
        menudata += (
            {'content': 'Contents',
             'href': contents_url,
             'selected': self.request.ACTUAL_URL == contents_url,
             },
            )

        if can_manage:
            menudata += (
                {'content': 'Preferences',
                 'href': prefs_url,
                 'selected': self.request.ACTUAL_URL == prefs_url,
                 },
                )

        team = proj.getTeams()[0]
        filter_states = tuple(team.getActiveStates()) + ('pending',)
        if self.member_info.get('id') not in team.getMemberIdsByStates(filter_states):
            # XXX this should be "if self.is_project_member():" but it breaks a test
            # which is really odd since the code is copied and pasted from here
            # so much for trying to fix things
            req_mship_url = '%s/request-membership' % proj.absolute_url()
            menudata += (
                {'content': 'Join project',
                 'href': req_mship_url,
                 'selected': self.request.ACTUAL_URL == req_mship_url,
                 'class': 'oc-topnav-join'
                 },
                )

        return menudata


    def is_flet_selected(self, flet):
        flet = flet.get('name')
        if flet == 'listen':
            lists_url = '/'.join((self.areaURL, 'lists'))
            return self.request.ACTUAL_URL.startswith(lists_url)
        elif flet == 'tasks':
            header = self.request.get_header('X-Openplans-Application')
            return header == 'tasktracker'
        elif flet == 'blog':
            header = self.request.get_header('X-Openplans-Application')
            return header == 'wordpress'
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
        mem_id = self.loggedinmember.getId()
        tm = ITransientMessage(self.portal)
        t_msgs = tm.get_all_msgs(mem_id)
        msg_count = sum([len(value) for key,value in t_msgs.iteritems() if not key == 'Trackback'])

        query = dict(portal_type='OpenMembership',
                     getId=mem_id,
                     )
        mship_brains = self.catalogtool(**query)
        proj_invites = [brain for brain in mship_brains if brain.review_state == 'pending' and brain.lastWorkflowActor != mem_id]
        
        return msg_count + len(proj_invites)

    @memoizedproperty
    def menudata(self):
        mem_data = self.member_info
        
        menudata = (

            {'content': 'Sign out',
             'href': '%s/logout' % self.siteURL,
             },

            )

        return menudata
