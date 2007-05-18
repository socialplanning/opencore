from opencore.nui.opencoreview import OpencoreView
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile

class WikiEdit(OpencoreView):
    wiki_edit = ZopeTwoPageTemplateFile('wiki-edit.pt')

    def update(self):
        self.errors = {}
        self.context.validate(REQUEST=self.request, errors=self.errors, data=1, metadata=0)
        if self.errors:
            self.portal_status_message='Please correct these errors.'
            return super(WikiEdit, self).__call__(errors=self.errors)
        
        self.context.processForm(values=self.request.form)
        self.request.response.redirect(self.context.absolute_url())

    def show(self):
        return self.wiki_edit()

    def canEdit(self):
        return self.user()['canedit']


class AttachmentView(OpencoreView):
    create_snippet = ZopeTwoPageTemplateFile('create-att.pt')
    delete_snippet = ZopeTwoPageTemplateFile('delete-att.pt')

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

    def createAtt(self):
        self.new_attachment = self.handle_createAtt()
        return self.create_snippet()
    
    def deleteAtt(self):
        self.context.manage_delObjects([self.request.form['attachment_id']])
        return self.delete_snippet()

    def handle_createAtt(self):
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



    def render_page_by_name(self, page):
        #if user_has_js:
        self.index = ZopeTwoPageTemplateFile(page)
        #else:
        #    self.index = ViewPageTemplateFile('wholething')
        self()
