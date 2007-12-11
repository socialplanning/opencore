from Acquisition import aq_inner
from Products.CMFCore.utils import getToolByName
from Products.Five.browser import metaconfigure, pagetemplatefile
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from Products.PageTemplates.PageTemplate import PageTemplate
from Products.listen.browser.mail_archive_views import ArchiveForumView, ArchiveDateView, \
                                                       ArchiveNewTopicView, SubFolderDateView, \
                                                       ArchiveSearchView
from Products.listen.browser.mail_message_views import ForumMailMessageView, ThreadedMailMessageView, \
                                                       MessageReplyView, SearchDebugView
from Products.listen.browser.manage_membership import ManageMembersView
from Products.listen.browser.moderation import ModerationView
from Products.listen.content import ListTypeChanged
from Products.listen.interfaces import IMailingList
from Products.listen.interfaces.list_types import PublicListTypeDefinition, \
                                                  PostModeratedListTypeDefinition, \
                                                  MembershipModeratedListTypeDefinition
from Products.listen.interfaces import IPublicList
from Products.listen.interfaces import IMembershipModeratedList
from Products.listen.interfaces import IPostModeratedList
from Products.listen.utilities.list_lookup import ListLookupView
from lxml.html.clean import Cleaner
from opencore.browser.formhandler import OctopoLite, action
from opencore.browser.base import BaseView, _
from opencore.listen.mailinglist import OpenMailingList
from opencore.listen.mailinglist_views import MailingListAddForm, MailingListEditForm, MailingListView
from plone.app.form import _named
from plone.memoize.view import memoize as req_memoize
from zope.app.annotation.interfaces import IAnnotations
from zope.app.component.hooks import getSite
from zope.event import notify
from zope.formlib.namedtemplate import INamedTemplate
from zope.interface import implements, directlyProvides
from zExceptions import BadRequest
import cgi
import re
import new
import os.path

_ml_type_to_workflow = {
    PublicListTypeDefinition : 'policy_open',
    PostModeratedListTypeDefinition : 'policy_moderated',
    MembershipModeratedListTypeDefinition : 'policy_closed',
    }

_workflow_to_ml_type = dict((y, x) for x, y in _ml_type_to_workflow.items())

class ListenBaseView(BaseView):
    @req_memoize
    def list_url(self):
        obj = self.context
        while not IMailingList.providedBy(obj):
            try:
                obj = obj.aq_parent
            except AttributeError:
                return ''
        return obj.absolute_url()            

    @req_memoize
    def list_title(self):
        obj = self.context
        while not IMailingList.providedBy(obj):
            try:
                obj = obj.aq_parent
            except AttributeError:
                return ''
        return obj.Title()            
        
    @property
    def portal_status_message(self):
        if hasattr(self, '_redirected'):
            return []
        plone_utils = self.get_tool('plone_utils')
        msgs = plone_utils.showPortalMessages()
        if msgs:
            msgs = [msg.message for msg in msgs]
        else:
            msgs = []
        req_psm = self.request.form.get("portal_status_message")
        req_psm2 = self.request.get("portal_status_message")
        if req_psm:
            req_psm = cgi.escape(req_psm)
            msgs.append(req_psm)
        elif req_psm2:
            req_psm2 = cgi.escape(req_psm2)
            msgs.append(req_psm2)

        return msgs

    def getSuffix(self):
        """
        Retrieves the FQDN that is the list address suffix for a site from
        the opencore_properties PropertySheet.  Requires a context object
        from inside the site so the properties tool can be retrieved.
        """
        # use threadlocal site to hook into acquisition context
        site = getSite()
        ptool = getToolByName(site, 'portal_properties')
        ocprops = ptool._getOb('opencore_properties')
        return '@' + str(ocprops.getProperty('mailing_list_fqdn').strip())

class ListAddView(ListenBaseView, OctopoLite):

    template = ZopeTwoPageTemplateFile('create.pt')

    @req_memoize
    def list_title(self):
        obj = self.context
        while not IMailingList.providedBy(obj):
            try:
                obj = obj.aq_parent
            except AttributeError:
                return ''
        return obj.Title()            
        
    @action('validate')
    def validate(self, target=None, fields=None):
        putils = getToolByName(self.context, 'plone_utils')
        errors = {}
        mailto = self.request.form.get('mailto')
        mailto = putils.normalizeString(mailto)
        if (self.context.has_key(mailto)):
            errors['oc-mailto-error'] = {
                'html': 'The requested list prefix is already taken.',
                'action': 'copy',
                'effects': 'highlight'
                }
        else:
            errors['oc-mailto-error'] = {
                'html': '',
                'action': 'copy',
                'effects': ''
                }
        return errors


    @action('add')
    def handle_request(self, target=None, fields=None):
        # Get the tool used to normalize strings
        putils = getToolByName(self.context, 'plone_utils')

        # Create an empty dictionary to hold any eventual errors.
        self.errors = {}

        # Let's do some form validation
        # Get and clean up title from request
        title = self.request.form.get('title', '')
        title = re.compile('\s+').sub(' ', title).strip()
        if not isinstance(title, unicode):
            title = unicode(title, 'utf-8')
        self.request.form['title'] = title

        # Get and check the list policies
        workflow = self.request.form.get('workflow_policy')
        if workflow not in ('policy_open', 'policy_moderated', 'policy_closed'):
            self.errors['workflow_policy'] = _(u'list_create_invalid_workflow_error', u'The mailing list security must be set to open, moderated, or closed.')

        archive = int(self.request.form.get('archival_policy'))
        if archive not in (0, 1, 2):
            self.errors['archive'] = _(u'list_create_invalid_archive_error', u'The mailing list archival method must be set to all, text-only, or none.')

        mailto = self.request.form.get('mailto')
        if not re.match('[a-zA-Z][-\w]+', mailto):
            self.errors['mailto'] = _(u'list_create_invalid_prefix_error', u'Only the following characters are allowed in list address prefixes: alpha-numerics, underscores, hyphens, and periods (i.e. A-Z, a-z, 0-9, and _-. symbols)')
        else:
            mailto = putils.normalizeString(mailto)
            if hasattr(self.context, mailto):
                self.errors['mailto'] = _(u'list_create_duplicate_error', u'The requested list prefix is already taken.')

        # If we don't pass sanity checks by this point, abort and let the user correct their errors.
        if self.errors:
            self.add_status_message(_(u'psm_correct_errors_below', u'Please correct the errors indicated below.'))
            return

        # Try to create a mailing list using the mailto address to see if it's going to be valid
        lists_folder = self.context
        try:
            lists_folder.invokeFactory(OpenMailingList.portal_type, mailto)
        except BadRequest:
            self.errors['mailto'] = _(u'list_create_duplicate_error', u'The requested list prefix is already taken.')
            self.add_status_message(_(u'psm_correct_errors_below', u'Please correct the errors indicated below.'))
            return

        list = lists_folder._getOb(mailto)

        if self.errors:
            self.add_status_message(_(u'psm_correct_errors_below', u'Please correct the errors indicated below.'))
            return 

        list.managers = (unicode(self.loggedinmember.getId()),)
        list.setDescription(unicode(self.request.form.get('description','')))

        old_workflow_type = list.list_type
        
        new_workflow_type = _workflow_to_ml_type[workflow]
            
        notify(ListTypeChanged(list,
                               old_workflow_type.list_marker,
                               new_workflow_type.list_marker))

        list.archived = archive

        self.template = None

        s_message_mapping = {'title': title}
        s_message = _(u'list_created',
                      u'"${title}" has been created.',
                      mapping=s_message_mapping)
        
        self.add_status_message(s_message)

        self.redirect(list.absolute_url())


class ListEditView(ListenBaseView, OctopoLite):
    template = ZopeTwoPageTemplateFile('edit.pt')

    @action('add')
    def handle_request(self, target=None, fields=None):
        #FIXME: refactor out form normalization stuff
        

        # Get the tool used to normalize strings
        putils = getToolByName(self.context, 'plone_utils')

        # Create an empty dictionary to hold any eventual errors.
        self.errors = {}

        # Let's do some form validation
        # Get and clean up title from request
        title = self.request.form.get('title', '')
        title = re.compile('\s+').sub(' ', title).strip()
        if not isinstance(title, unicode):
            title = unicode(title, 'utf-8')
        self.request.form['title'] = title

        # Get and check the list policies
        workflow = self.request.form.get('workflow_policy')
        if workflow not in ('policy_open', 'policy_moderated', 'policy_closed'):
            self.errors['workflow_policy'] = _(u'list_create_invalid_workflow_error', u'The mailing list security must be set to open, moderated, or closed.')

        archive = int(self.request.form.get('archival_policy'))
        if archive not in (0, 1, 2):
            self.errors['archive'] = _(u'list_create_invalid_archive_error', u'The mailing list archival method must be set to all, text-only, or none.')

        mailto = self.request.form.get('mailto')
        if not re.match('[a-zA-Z][-\w]+', mailto):
            self.errors['mailto'] = _(u'list_create_invalid_prefix_error', u'Only the following characters are allowed in list address prefixes: alpha-numerics, underscores, hyphens, and periods (i.e. A-Z, a-z, 0-9, and _-. symbols)')
        else:
            mailto = putils.normalizeString(mailto)
            if hasattr(self.context, mailto):
                self.errors['mailto'] = _(u'list_create_duplicate_error', u'The requested list prefix is already taken.')

        # If we don't pass sanity checks by this point, abort and let the user correct their errors.
        if self.errors:
            self.add_status_message(_(u'psm_correct_errors_below', u'Please correct the errors indicated below.'))
            return

        list = self.context

        if self.errors:
            self.add_status_message(_(u'psm_correct_errors_below', u'Please correct the errors indicated below.'))
            return 

        #fixme: set managers

        list.setDescription(unicode(self.request.form.get('description','')))

        list.mailto = mailto

        old_type = list.list_type        
        new_type = _workflow_to_ml_type[workflow]
            
        notify(ListTypeChanged(list,
                               old_type.list_marker,
                               new_type.list_marker))

        list.archived = archive
        self.template = None

        s_message = _(u'list_preferences_updated',
                      u'Your changes have been saved.')
        
        self.add_status_message(s_message)

        self.redirect(list.absolute_url() + "/edit")

    def workflow_policy(self):
        return _ml_type_to_workflow[self.context.list_type]

    def mailto(self):
        return self.context.mailto.split("@")[0]

# uh.. if you are going write meta factories you should write tests too
# isn't this what super and mixins are is suppose to solve?
def make_nui_listen_view_class(ListenClass, set_errors=False, add_update=False):
    class NuiListenView(ListenBaseView, ListenClass):
        # mask the property defined in any listen views
        context = None
        def __init__(self, context, request):
            self.context = context # MUST set context before calling the ListenClass constructor
            ListenClass.__init__(self, context, request)
            BaseView.__init__(self, context, request)

            psm = self.request.get('portal_status_message')
            
            if set_errors:
                self.errors = ()

        if add_update:
            def update(self):
                result = super(NuiListenView, self).update()
                if self.status and self.errors:
                    self.addPortalStatusMessage(self.status)
                return result

        def body(self):
            body = ListenClass.body(self)
            cleaner = Cleaner()
            body = cleaner.clean_html(body)
            if body.startswith('<p>'):
                body = body[3:-4]
            return body
    
    return NuiListenView

# prefixing everything is unnecessary
NuiMailingListView = make_nui_listen_view_class(MailingListView)
NuiMailingListAddView = make_nui_listen_view_class(MailingListAddForm, set_errors=True, add_update=True)
NuiMailingListEditView = make_nui_listen_view_class(MailingListEditForm, set_errors=True, add_update=True)


from Products.listen.interfaces import IMembershipPendingList
from zope.component import getAdapter

class ArchiveForumView(make_nui_listen_view_class(ArchiveForumView)):
    """puke a little, inherit"""
    def subscription_snippet(self):
        the_list = aq_inner(self.context).aq_parent
        return the_list.restrictedTraverse("subscription_snippet")()

NuiArchiveDateView = make_nui_listen_view_class(ArchiveDateView)
NuiArchiveNewTopicView = make_nui_listen_view_class(ArchiveNewTopicView)
NuiSubFolderDateView = make_nui_listen_view_class(SubFolderDateView)
NuiThreadedMailMessageView = make_nui_listen_view_class(ThreadedMailMessageView)
NuiForumMailMessageView = make_nui_listen_view_class(ForumMailMessageView)
NuiMessageReplyView = make_nui_listen_view_class(MessageReplyView)
NuiManageMembersView = make_nui_listen_view_class(ManageMembersView)
NuiModerationView = make_nui_listen_view_class(ModerationView)
NuiSearchDebugView = make_nui_listen_view_class(SearchDebugView)
NuiArchiveSearchView  = make_nui_listen_view_class(ArchiveSearchView)
NuiListLookupView = make_nui_listen_view_class(ListLookupView)


##########################################################################
# We're overriding the default NamedTemplateAdapter to work around a
# bug in plone.app.form._named.  The bug has been fixed on the Plone
# trunk.
##########################################################################

class NamedTemplateAdapter(object):
    """A named template adapter implementation that has the ability
    to lookup the template portion from regular traversal (intended for
    being able to customize the template portion of a view component
    in the traditional portal_skins style).
    """

    implements(INamedTemplate)

    def __init__(self, context):
        self.context = context

    def __call__(self, *args, **kwargs):
        """
        use aq_inner of the innermost context so we don't get a
        circular acquisition context.
        """
        view = self.context.__of__(self.context.context.aq_inner)
        cleanup = []

        # basically this means we only do customized template lookups
        # for views defined with <browser:page template='foo'> 
        if isinstance(view, metaconfigure.ViewMixinForTemplates) and \
               _named.try_portal_skins:
            index = getattr(view, 'index', None)
            if index is not None:
                name = _named.proper_name(index.filename)
                try:
                    template = view.context.portal_url.getPortalObject().restrictedTraverse(name)
                except AttributeError:
                    # ok, we couldn't find a portal_skins defined item
                    # so we fall back to the defined page template
                    template = index
                else:
                    if isinstance(getattr(template, 'aq_base', object()), PageTemplate):
                        template = _named.ViewTemplateFromPageTemplate(template,
                                                                       view.context)
                        template = template.__of__(view)
                    else:
                        template = index

            result = template(*args, **kwargs)
            return result
        else:
            return self.default_template.__of__(view)(*args, **kwargs)


def named_template_adapter(template):
    """Return a new named template adapter which defaults the to given
    template.
    """

    new_class = new.classobj('GeneratedClass', 
                             (NamedTemplateAdapter,),
                             {})
    new_class.default_template = template

    return new_class

path_prefix = os.path.split(_named.__file__)[0]
_path = os.path.join(path_prefix, 'pageform.pt')
_template = pagetemplatefile.ViewPageTemplateFile(_path)
default_named_template_adapter = named_template_adapter(_template)

_subpage_path = os.path.join(path_prefix, 'subpageform.pt')
_subpage_template = pagetemplatefile.ViewPageTemplateFile(_subpage_path)
default_subpage_template = named_template_adapter(_subpage_template)
