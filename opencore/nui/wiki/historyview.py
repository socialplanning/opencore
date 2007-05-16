from opencore.nui.opencoreview import OpencoreView
from opencore.nui import htmldiff2
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile

class WikiVersionCompare(OpencoreView):

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
        return self.version_compare()

    def get_version(self, version_id):
        version_id = int(version_id)
        pr = self.context.portal_repository
        return pr.retrieve(self.context, version_id)

    def get_page(self, version_id):
        pr = self.context.portal_repository
        doc = pr.retrieve(self.context, version_id)
        return doc.object
        

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
            

class WikiHistory(OpencoreView):

    def get_versions(self):
        """
        Returns a list of versions on the object.
        """
        pr = self.context.portal_repository
        return pr.getHistory(self.context, countPurged=False)
    

