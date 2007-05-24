from opencore.nui.opencoreview import OpencoreView
from opencore.nui.wiki import htmldiff2
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from DateTime import DateTime
from topp.utils.pretty_date import prettyDate

class WikiVersionView(OpencoreView): 

    def get_page(self, version_id):
        pr = self.context.portal_repository
        doc = pr.retrieve(self.context, version_id)
        return doc.object
        
    def get_versions(self):
        """
        Returns a list of versions on the object.
        """
        pr = self.context.portal_repository
        return pr.getHistory(self.context, countPurged=False)

    def get_version(self, version_id):
        version_id = int(version_id)
        pr = self.context.portal_repository
        return pr.retrieve(self.context, version_id)

    def version_title(self, version_id): 
        if version_id == 0:
            return "Initial"
        elif version_id == self.current_id():
            return "Current"
        else: 
            return "Version %d" % version_id

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

    version_compare = ZopeTwoPageTemplateFile('wiki-version-compare.pt')
    # FIXME: there's probably something generic like this already.
    generic_error = ZopeTwoPageTemplateFile('wiki-generic-error.pt')

    def __call__(self):
        versions = self.request.get('version_id')
        req_error = None
        if not versions:
            req_error = 'You did not check any versions in the version compare form'
        elif not isinstance(versions, list) or len(versions) < 2:
            req_error = 'You did not check enough versions in the version compare form'
        elif len(versions) > 2:
            req_error = 'You may only check two versions in the version compare form'
        if req_error:
            self.portal_status_message = [req_error]
            # FIXME: It's really a 400 Bad Request that we should be
            # sending here (with an error message):
            return self.generic_error()
        versions.sort()
        self.old_version_id, self.new_version_id = self.sort_versions(*versions)

        pr = self.context.portal_repository
        # FIXME: catch exceptions when getting a version that doesn't exist
        self.old_version = self.get_version(self.old_version_id)
        self.new_version = self.get_version(self.new_version_id)

        old_page = self.get_page(self.old_version_id)
        new_page = self.get_page(self.new_version_id)
        self.html_diff = htmldiff2.htmldiff(old_page.EditableBody(), 
                                            new_page.EditableBody())

        self.old_next_enabled = self.old_version_id + 1 < self.new_version_id
        self.old_prev_enabled = self.old_version_id > 0
        self.new_next_enabled = self.new_version_id < self.current_id() 
        self.new_prev_enabled = self.old_next_enabled


        return self.version_compare()

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



    

