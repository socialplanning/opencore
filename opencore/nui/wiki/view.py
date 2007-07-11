from opencore.nui.base import BaseView
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from opencore.nui.formhandler import button

class WikiEdit(BaseView):

    @button('save')
    def handle_request(self):
        self.errors = {}
        self.context.validate(REQUEST=self.request, errors=self.errors, data=1, metadata=0)
        if self.errors:
            for msg in self.errors.values():
                self.addPortalStatusMessage(msg)
            return self.errors
        
        self.context.processForm(values=self.request)
        repo = self.context.portal.portal_repository
        repo.save(self.context, comment = self.request.form.get('comment', ''))
        self.addPortalStatusMessage(u'Changes saved.')
        self.redirect(self.context.absolute_url())


class AttachmentView(BaseView):
    attachment_snippet = ZopeTwoPageTemplateFile('attachment.pt')
    create_snippet = ZopeTwoPageTemplateFile('create-att.pt')
    failed_snippet = ZopeTwoPageTemplateFile('failed.pt')
    delete_snippet = ZopeTwoPageTemplateFile('delete-att.pt')

    def attachment_url(self):
        return "%s/@@attachmentSnippet?attachment_id=%s" % (self.context.absolute_url(), self.new_attachment().id)

    def attachmentSnippet(self):
        attachment = self.context._getOb(self.request.form.get('attachment_id'))
        self.new_attachment = lambda: attachment
        return self.attachment_snippet()
    
    def handle_updateAtt(self):
        attach_id = self.request.form.get('attachment_id')
        attachment = self.context._getOb(attach_id)
        title = self.request.form.get('attachment_title') or attach_id
        attachment.setTitle(title)
        attachment.reindexObject()
        return attachment

    def updateAtt(self):
        """do not assign directly because this will implicitly wrap the
        attachment in the view.  """
        new_attachment = self.handle_updateAtt()
        self.new_attachment = lambda: new_attachment
        return self.attachment_snippet()

    def createAtt(self):
        new_attachment = self.handle_createAtt()

        if new_attachment is None:
            return self.failed_snippet()
        
        self.new_attachment = lambda: new_attachment

        return self.create_snippet()
    
    def deleteAtt(self):
        self.context.manage_delObjects([self.request.form.get('attachment_id')])
        return self.delete_snippet()

    def handle_createAtt(self):
        attachmentTitle = self.request.form.get('attachmentTitle', None)
        attachmentFile = self.request.form.get('attachmentFile', None)
        
        if not attachmentFile:
            self.errors = {'attachmentFile' : 'you forgot to upload something'}
            return None 
        
#         # Make sure we have a unique file name
        fileName = attachmentFile.filename
        
        imageId = ''

        if fileName:
            fileName = fileName.split('/')[-1]
            fileName = fileName.split('\\')[-1]
            fileName = fileName.split(':')[-1]
            plone_utils = self.get_tool('plone_utils')
            imageId = plone_utils.normalizeString(fileName)
            
        if not imageId:
            imageId = plone_utils.normalizeString(attachmentTitle)
            
        imageId = self.findUniqueId(imageId)
        
        newImageId = self.context.invokeFactory(id = imageId, type_name = 'FileAttachment')
        if newImageId is not None and newImageId != '':
            imageId = newImageId
            
        object = self.context._getOb(imageId, None)
        object.setTitle(self.findUniqueTitle(attachmentTitle or imageId))
        object.setFile(attachmentFile)
        object.reindexObject()
        return object

    def findUniqueTitle(self, title):
        titles = [self.context._getOb(i).Title() for i in self.context.objectIds()]
 
        def getVersion(title, number):
            """returns the version string of a title"""
            delimiter = ' v'
            try:
                version = int(title.rsplit(delimiter, 1)[1])
                title = title.rsplit(delimiter,1)[0]
            except (IndexError, ValueError):
                pass
            return delimiter.join((title, str(number)))

        idx = 0
        while True:
            if not title in titles:
                return title
            title = getVersion(title, idx)
            idx += 1

    def findUniqueId(self, id):
        contextIds = self.context.objectIds()

        if id not in contextIds:
            return id

        dotDelimited = id.split('.')

        ext = dotDelimited[-1]
        name = '.'.join(dotDelimited[:-1])

        idx = 0
        while ('%s.%s.%s' % (name, str(idx), ext)) in contextIds:
            idx += 1

        return ('%s.%s.%s' % (name, str(idx), ext))
