from opencore.nui.base import BaseView
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile

class WikiEdit(BaseView):

    def __call__(self):
        self.errors = {}
        self.context.validate(REQUEST=self.request, errors=self.errors, data=1, metadata=0)
        if self.errors:
            self.addPortalStatusMessage('Please correct the indicated errors.')
            return super(WikiEdit, self).__call__(errors=self.errors)
        
        self.context.processForm(values=self.request)
        repo = self.context.portal.portal_repository
        repo.save(self.context, comment = self.request.get('comment', ''))
        self.request.response.redirect(self.context.absolute_url())


class AttachmentView(BaseView):
    attachment_snippet = ZopeTwoPageTemplateFile('attachment.pt')
    create_snippet = ZopeTwoPageTemplateFile('create-att.pt')
    failed_snippet = ZopeTwoPageTemplateFile('failed.pt')
    delete_snippet = ZopeTwoPageTemplateFile('delete-att.pt')

    def attachment_url(self):
        return "%s/@@attachmentSnippet?attachment_id=%s" % (self.context.absolute_url, self.new_attachment().id)

    def attachmentSnippet(self):
        attachment = self.context._getOb(self.request.get('attachment_id'))
        self.new_attachment = lambda: attachment
        return self.attachment_snippet()
    
    def handle_updateAtt(self):
        attachment = self.context._getOb(self.request.get('attachment_id'))
        attachment.setTitle(self.request.get('attachment_title'))
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
        self.context.manage_delObjects([self.request.get('attachment_id')])
        return self.delete_snippet()

    def handle_createAtt(self):
         attachmentTitle = self.request.get('attachmentTitle', None)
         attachmentFile = self.request.get('attachmentFile', None)

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
         object.setTitle(attachmentTitle)
         object.setFile(attachmentFile)
         object.reindexObject()
         return object

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
