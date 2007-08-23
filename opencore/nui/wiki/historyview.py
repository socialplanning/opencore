from zExceptions import Redirect
from Products.CMFCore.utils import getToolByName
from Products.CMFEditions.interfaces.IArchivist import ArchivistRetrieveError
from opencore.nui.base import BaseView
from opencore.nui.wiki import htmldiff2
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from DateTime import DateTime
from topp.utils.pretty_date import prettyDate
from plone.memoize import instance
from view import WikiBase


# XXX i18n 


class WikiVersionView(WikiBase): 

    def __init__(self, context, request):
        BaseView.__init__(self, context, request)
        self.pr = self.get_tool('portal_repository')

    def get_page(self, version_id):
        doc = self.pr.retrieve(self.context, version_id)
        return doc.object
        
    def get_versions(self):
        """
        Returns a list of versions on the object.
        """
        return self.pr.getHistory(self.context, countPurged=False)

    def get_version(self, version_id):
        version_id = int(version_id)
        return self.pr.retrieve(self.context, version_id)

    def version_title(self, version_id): 
        if version_id == 0:
            return "Initial Version"
        elif version_id == self.current_id():
            return "Current Version"
        else: 
            return "Version %d" % (version_id + 1)

    def current_id(self): 
        return len(self.get_versions()) - 1

    def previous_id(self, version_id): 
        if version_id == 0:
            return None
        else:
            return version_id - 1
    
    def next_id(self, version_id): 
        if version_id == self.current_id():
            return None
        else:
            return version_id + 1
            
    def pretty_mod_date(self, version):
        return prettyDate(DateTime(version.sys_metadata['timestamp']))



class WikiVersionCompare(WikiVersionView):

    @instance.memoizedproperty
    def versions(self):
        versions = self.request.form.get('version_id')
        req_error = None
        if not versions:
            req_error = 'choose two versions'
        elif not isinstance(versions, list) or len(versions) < 2:
            req_error = 'choose two versions'
        elif len(versions) > 2:
            req_error = 'choose only two versions'
        if not req_error:
            versions.sort()
            old_version_id, new_version_id = self.sort_versions(*versions)
            try:
                old_version = self.get_version(old_version_id)
                new_version = self.get_version(new_version_id)
            except ArchivistRetrieveError:
                req_error = 'invalid version'
            
        if req_error:
            # redirect to input page on error
            self.add_status_message(req_error)
            raise Redirect('%s/history' % self.context.absolute_url())
        
        return dict(old=(old_version_id, old_version),
                    new=(new_version_id, new_version))

    def handle_diff(self):
        self.old_version_id, self.old_version = self.versions['old']
        self.new_version_id, self.new_version = self.versions['new']
        old_page = self.get_page(self.old_version_id)
        new_page = self.get_page(self.new_version_id)
        self.html_diff = htmldiff2.htmldiff(old_page.EditableBody(), 
                                            new_page.EditableBody())

        self.old_next_enabled = self.old_version_id + 1 < self.new_version_id
        self.old_prev_enabled = self.old_version_id > 0
        self.new_next_enabled = self.new_version_id < self.current_id() 
        self.new_prev_enabled = self.old_next_enabled

    def sort_versions(self, v1, v2):
        """
        Return older_version, newer_version
        """

        v1 = int(v1)
        v2 = int(v2)
        if v1 > v2:
            return v2, v1
        else:
            return v1, v2

    def __call__(self, *args, **kwargs):
        self.handle_diff()
        return super(BaseView, self).__call__(*args, **kwargs)


class WikiVersionRevert(WikiVersionView):

    def __call__(self, *args, **kwargs):

        # error check parameters
        req_error = None
        view_url = self.context.absolute_url()
        
        try:
            version_id = int(self.request.form.get('version_id'))
            if version_id < 0 or version_id >= self.current_id():
                req_error = 'invalid version'
        except:
            req_error = 'invalid version'

        # bail out on error 
        if req_error is not None:
            self.add_status_message(req_error)
            raise Redirect(view_url)

        # actually do the revert

        self.pr.revert(self.context, version_id)

        # XXX this should use topp.messages.psm['rolled back']        
        message = "Rolled back to %s" % self.version_title(version_id)

        if self.pr.supportsPolicy(self.context, 'version_on_revert'):
            self.pr.save(obj=self.context, comment=message)


        # send user to the view page 
        self.add_status_message(message)
        self.request.RESPONSE.redirect(view_url)
