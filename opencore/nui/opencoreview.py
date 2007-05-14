"""
OpencoreView: the base view for all of opencore's new zope3 views.
"""
import nui

from opencore.content.page import OpenPage
from opencore.content.member import OpenMember
from Products.OpenPlans.content.project import OpenProject
from Products.CMFCore.permissions import ModifyPortalContent
from Products.CMFCore.utils import getToolByName
from Products.Five import BrowserView
from memojito import memoize, memoizedproperty
from opencore import redirect 
from opencore.interfaces import IProject 
from zope.component import getMultiAdapter, adapts, adapter
from topp.utils.pretty_text import truncate
from zope.app.pagetemplate import ViewPageTemplateFile
class OpencoreView(BrowserView):
    def __init__(self, context, request):
        self.context      = context
        self.request      = request
        self.transcluded  = request.get_header('X-transcluded')
        self.membranetool = getToolByName(context, 'membrane_tool')
        self.membertool   = getToolByName(context, 'portal_membership')
        self.catalogtool  = getToolByName(context, 'portal_catalog')
        self.portal       = getToolByName(context, 'portal_url').getPortalObject()
        self.sitetitle    = self.portal.title
        self.siteURL      = self.portal.absolute_url()
        self.logoURL      = nui.logoURL
        self.dob          = nui.dob
        self.piv = context.unrestrictedTraverse('project_info') # TODO don't rely on this
        self.miv = context.unrestrictedTraverse('member_info')  # TODO don't rely on this
        self.errors = {}

    def portal_status_message(self):
        plone_utils = getToolByName(self.context, 'plone_utils')
        msgs = plone_utils.showPortalMessages()
        msgs = [msg.message for msg in msgs]
        return msgs

    def include(self, viewname):
        if self.transcluded:
            return nui.renderTranscluderLink(viewname)
        return nui.renderView(self.getViewByName(viewname))
    
    # deprecated
    def magicTopnavSubcontext(self): # TODO get rid of magic inference
        if self.inproject():
            return 'oc-topnav-subcontext-project'
        elif self.inuser():
            return 'oc-topnav-subcontext-user'
        return 'oc-blank'

    #deprecated
    def magicContent(self): # TODO get rid of magic inference
        if self.inproject():
            return 'oc-project-view'
        elif self.inuser():
            return 'oc-user-profile'
        return 'oc-blank'

    def renderTopnavSubcontext(self, viewname):
        viewname = viewname or self.magicTopnavSubcontext()
        return nui.renderView(self.getViewByName(viewname))

    def renderContent(self, viewname):
        viewname = viewname or self.magicContent()
        return nui.renderView(self.getViewByName(viewname))

    def renderProjectContent(self):
        return nui.renderOpenPage(self.currentProjectPage())

    def getViewByName(self, viewname):
        return self.context.unrestrictedTraverse('@@' + viewname)


    def projectobj(self): # TODO
        return self.piv.project

    def userobj(self):
        return self.membertool.getAuthenticatedMember()

    def loggedin(self):
        return self.userobj().getId() is not None

    def inproject(self): # TODO
        return self.piv.inProject

    def inuser(self): # TODO
        return self.miv.inMemberArea
    
    def vieweduser(self): # TODO
        """Returns the user found in the context's acquisition chain, if any."""
        return self.miv.member

    def pagetitle(self):
        if self.inproject():
            return self.currentProjectPage().title
        return self.context.title # TODO?

    def areatitle(self):
        if self.inproject():
            return self.project()['fullname']
        if self.inuser():
            return self.vieweduser().fullname
        return self.context.title # TODO?

    def windowtitle(self):
        pagetitle, areatitle = truncate(self.pagetitle(), max=24), \
                               truncate(self.areatitle(), max=16)
        titles = [pagetitle, areatitle, self.sitetitle]
        return nui.windowTitleSeparator.join([i for i in titles if i])

    def pageURL(self):
        if self.inproject():
            return self.currentProjectPage().absolute_url()
        return self.context.absolute_url() # TODO?

    def areaURL(self):
        if self.inproject():
            return self.project()['url']
        if self.inuser():
            return self.user()['url']
        else: # TODO
            return ''

    def nusers(self): # TODO cache
        """Returns the number of users of the site."""
        users = self.membranetool(getId='')
        return len(users)

    def nprojects(self): # TODO cache
        """Returns the number of projects hosted by the site."""
        projects = self.catalogtool(portal_type='OpenProject')
        return len(projects)

    def user(self):
        """Returns a dict containing information about the
        currently-logged-in user for easy template access.
        If no user is logged in, there's just less info to return."""
        if self.loggedin():
            usr = self.userobj()
            id = usr.getId()
            user_dict = dict(id=id,
                             fullname=usr.fullname,
                             url=self.membertool.getHomeUrl(),
                             )
            # XXX admins don't have as many properties, so we have a special case for them
            # right now checking for string 'admin', we should check if the user has the right role instead
            if id == 'admin':
                user_dict['canedit'] = True
                return user_dict
            else:
                canedit = bool(self.membertool.checkPermission(ModifyPortalContent, self.context))
                user_dict.update(dict(canedit=canedit,
                                      lastlogin=usr.getLast_login_time(),
                                      ))
                return user_dict
        return dict(canedit=False)

    def canEdit(self):
        return self.user()['canedit']

    def project(self): # TODO
        """Returns a dict containing information about the
        currently-viewed project for easy template access."""
        if self.inproject():
            proj = self.projectobj()
            return dict(navname=proj.getId(),
                        fullname=proj.getFull_name(),
                        url=proj.absolute_url(), # XXX use self.projectHomePage.absolute_url() instead?
                        home=self.projectHomePage(),
                        featurelets=self.projectFeaturelets())

    def page(self): # TODO
        """Returns a dict containing information about the
        currently-viewed page for easy template access."""
        if self.inproject():
            page = self.currentProjectPage()
            lastModifiedOn = '1/13/37'
            lastModifiedBy = 'jab'
            if page:
                return dict(title=page.title,
                            url=page.absolute_url(),
                            lastModifiedOn=lastModifiedOn,
                            lastModifiedBy=lastModifiedBy)


    def projectHomePage(self):
        if self.inproject():
            homepagename = self.projectobj().getDefaultPage()
            return self.projectobj().unrestrictedTraverse(homepagename)

    def projectFeaturelets(self): # TODO
        featurelets = []
        featurelets.append({'name': 'featurelet1', 'url': ''})
        featurelets.append({'name': 'featurelet2', 'url': ''})
        return featurelets

    def currentProjectPage(self):
        if self.inproject():
            if isinstance(self.context, OpenProject):
                return self.projectHomePage()
            elif isinstance(self.context, OpenPage):
                return self.context
            else: # TODO
                return 'Unexpected error in OpencoreView.currentProjectPage: ' \
                       'self.context is neither an OpenProject nor an OpenPage'
    
    def user_exists(self, username):
        users = self.membranetool(getId=username)
        return len(users) > 0

    def userExists(self):
        username = self.request.get("username")
        if username is not None:
            return self.user_exists(username)
        return False

class ProjectEditView(OpencoreView):
    wiki_edit = ZopeTwoPageTemplateFile('wiki-edit.pt')

    def update(self):
        self.errors = {}
        self.context.validate(REQUEST=self.request, errors=self.errors, data=1, metadata=0)
        if self.errors:
            self.portal_status_message='Please correct these errors.'
            return super(ProjectEditView, self).__call__(errors=self.errors)
        
        self.context.processForm(values=self.request.form)
        self.request.response.redirect(self.context.absolute_url())

    def show(self):
        return self.wiki_edit()

class AttachmentView(OpencoreView):
    create_snippet = ZopeTwoPageTemplateFile('create-att.pt')

    def handle_updateAtt(self):
        attachment = self.context._getOb(self.request.form['attachment_id'])
        attachment.setTitle(self.request.form['attachment_title'])
        attachment.reindexObject()
        return attachment
    
    def updateAtt(self):
        """do not assign directly because this will implicitly wrap the
        attachment in the view.  """

        self.new_attachment = lambda : self.handle_updateAtt() 
        return self.create_snippet()

    def handle_createAtt(self):
        return "not done yet"

    def createAtt(self):
        self.new_attachment = self.handle_createAtt()
        return self.create_snippet()

# We're not actually doing this yet.
#     def noJS(self):
#         action = self.request.form.get('action')
#         if not action in ['updateAtt', 'createAtt', 'deleteAtt']:
#             return 

#         if self.request.method == "POST":
#             getattr(self, 'handle_' + action)()
#             return self.whole_page()
#         else:
#             self.action = action
#             return self.confirm(*args, **kwargs)

    
    def deleteAtt(self):
        self.context.manage_delObjects([attachmentId])

    def createAtt(self):
         attachmentTitle = self.request.get('attachment_title')
         attachmentFile = self.request.get('attachment_file')

         if not attachmentFile:
             self.errors = {'attachment_file' : 'you forgot to upload something'}

#         # Make sure we have a unique file name
         fileName = attachmentFile.filename

         imageId = ''

         if fileName:
             fileName = fileName.split('/')[-1]
             fileName = fileName.split('\\')[-1]
             fileName = fileName.split(':')[-1]

#             imageId = plone_utils.normalizeString(fileName)

#         if not imageId:
#             imageId = plone_utils.normalizeString(attachmentTitle)

#         imageId = findUniqueId(imageId)

#         newImageId = new_context.invokeFactory(id = imageId, type_name = 'FileAttachment')
#         if newImageId is not None and newImageId != '':
#             imageId = newImageId

#         object = getattr(new_context, imageId, None)
#         object.setTitle(attachmentTitle)
#         object.setFile(attachmentFile)
#         object.reindexObject()

class YourProjectsView(OpencoreView):

    def get_projects_for_user(self):
        member = self.userobj()
        id = member.getId()
        if id is None: return []
        projects = member.getProjectListing()
        out = []
        for project in projects:
            roles = ', '.join(project.getTeamRolesForAuthMember())
            teams = project.getTeams()
            for team in teams:
                # eventually this will be 1:1 relationship, project:team
                mship = team.getMembershipByMemberId(id)
                if mship is not None:
                    created = mship.created()

            out.append({'title':project.title, 'role':roles, 'since':created, 'status':'not set'})
        return out

    def get_invitations_for_user(self):
        invites = []
        invites.append({'name':'Big Animals'})
        invites.append({'name':'Small Animals'})
        return invites
