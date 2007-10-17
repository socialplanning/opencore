from zope.event import notify
from zope.app.event import objectevent
from opencore.nui.base import BaseView
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from opencore.nui.formhandler import button, OctopoLite, action
from opencore.interfaces import IAmExperimental
from PIL import Image
from StringIO import StringIO
from lxml.html.clean import clean_html
from opencore.interfaces.catalog import ILastModifiedAuthorId
from topp.utils.pretty_date import prettyDate

class WikiBase(BaseView):

    def fileAttachments(self):
        path = '/'.join(self.context.getPhysicalPath())
        brains = self.catalog(portal_type='FileAttachment',
                              path=path,
                              )
        return brains

    def wiki_window_title(self, mode='view'):
        """see http://trac.openplans.org/openplans/ticket/588.
        mode should be one of: 'view', 'edit', or 'history'."""
        if mode == 'view':
            mode = ''
        else:
            mode = '(%s) ' % mode

        context = self.context

        if self.inmember:
            vmi = self.viewed_member_info

            # if viewing member homepage
            if mode:
                return '%s %s' % (context.Title(), mode)

            if vmi['home_url'] == context.absolute_url():
                return '%s on OpenPlans' % vmi['id']
            else:
                return '%s - %s on OpenPlans' % (context.Title(), vmi['id'])

        else:
            return '%s %s- %s' % (context.Title(), mode, self.area.Title())

    def lastModifiedTime(self):
        return prettyDate(self.context.ModificationDate())

    def lastModifiedAuthor(self):
        return ILastModifiedAuthorId(self.context)

class WikiView(WikiBase):
    displayLastModified = True # see wiki_macros.pt

    view_attachments_snippet = ZopeTwoPageTemplateFile('attachment-view.pt')

class WikiEdit(WikiBase, OctopoLite):

    kupu_template = ZopeTwoPageTemplateFile("wiki-edit.pt")
    xinha_template = ZopeTwoPageTemplateFile("wiki-edit-xinha.pt")

    attachment_snippet = ZopeTwoPageTemplateFile('attachment.pt')

    @property
    def template(self):
        # parent can be either a project, or a member folder
        # in either case, the behavior works properly
        parent = self.context.aq_inner.aq_parent
        if IAmExperimental.providedBy(parent):
            return self.xinha_template
        else:
            return self.kupu_template

    def _clean_html(self, html):
        """ delegate cleaning of html to lxml """
        return clean_html(html)

    @action('save')
    def handle_save(self, target=None, fields=None):
        self.create_attachment()

        self.errors = {}
        self.context.validate(REQUEST=self.request, errors=self.errors, data=1, metadata=0)
        if self.errors:
            for msg in self.errors.values():
                self.addPortalStatusMessage(msg)
            return self.errors

        allowed_params = set(['comment', 'oc-target', 'text_file', 'title', 'text', 'attachmentFile', 'submitted', 'text_text_format', 'attachmentTitle', 'task|save'])
        new_form = {}
        for k in self.request.form:
            if k in allowed_params:
                new_form[k] = self.request.form[k]
        
        # don't call process form, because we do our own cleaning of html
        # self.context.processForm(values=self.request)

        page_title = new_form['title']
        page_text = new_form['text']
        # XXX check description on news page
        description = new_form.get('description', None)
        clean_text = self._clean_html(page_text)

        self.context.setTitle(page_title)
        self.context.setText(clean_text)
        if description is not None:
            self.context.setDescription(description)

        # this updates things like last modified author on a wiki page
        # it's important to do this before the repo saves the new version
        notify(objectevent.ObjectModifiedEvent(self.context))


        repo = self.context.portal.portal_repository
        repo.save(self.context, comment = self.request.form.get('comment', ''))
        self.context.reindexObject()
        self.addPortalStatusMessage(u'Your changes have been saved.')

        # XXX is setting the template to None necessary?
        # it causes problems because it's more convenient to make template
        # a property now, which can't be set to None
        # self.template = None
        self.redirect(self.context.absolute_url())

    def _handle_createAtt(self):
        attachmentTitle = self.request.form.get('attachmentTitle')
        attachmentFile = self.request.form.get('attachmentFile')
        
        if not attachmentFile:
            self.errors = {'attachmentFile' : 'You forgot to upload something.'}
            return None 
        
        # Make sure we have a unique file name
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
            
        imageId = self._findUniqueId(imageId)
        
        newImageId = self.context.invokeFactory(id = imageId, type_name = 'FileAttachment')
        if newImageId is not None and newImageId != '':
            imageId = newImageId
            
        object = self.context._getOb(imageId, None)
        object.setTitle(self._findUniqueTitle(attachmentTitle or imageId))
        object.setFile(attachmentFile)
        object.reindexObject()
        return object

    def _findUniqueTitle(self, title):
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

    def _findUniqueId(self, id):
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
    
    @action('upload-attachment')
    def create_attachment(self, target=None, fields=None):
        new_attachment = self._handle_createAtt()

        if new_attachment is None:
            return {"An error": ""}

        my_attachment = lambda: new_attachment
        snippet = self.attachment_snippet(attachment=my_attachment)
        return {"oc-wiki-attachments":
                    {'action': 'append',
                     'effects': 'highlight',
                     'html': snippet
                     }
                }
    
    def _handle_updateAtt(self, attach_id, title):
        attachment = self.context._getOb(attach_id)
        attachment.setTitle(title)
        attachment.reindexObject('Title')
        return attachment

    @action('update-attachment')
    def update_attachment(self, target=None, fields=None):
        ### 
        # do not assign directly because thism will implicitly
        # wrap the attachment in the view.
        commands = {}
        if not target or not fields: return commands
        for obj_id, data in zip(target, fields):
            new_attachment = self._handle_updateAtt(obj_id, data.get('title', obj_id))
            my_attachment = lambda: new_attachment
            snippet = self.attachment_snippet(attachment=my_attachment)
            commands['%s_list-item' % obj_id] = {'action': 'replace',
                                                 'effects': 'highlight',
                                                 'html': snippet}
        return commands

    def display_delete_for(self, attachment):
        """
        decides whether to show the delete button
        next to an attachment. 
        """

        # XXX faster way? we know the id...
        att = self.context._getOb(attachment.id)
        return self.get_tool('portal_membership').checkPermission('Delete objects', att)

    @action('delete-attachment')
    def delete_attachment(self, target=None, fields=None):
        survivors = list(target)
        self.context.manage_delObjects(survivors)
        commands = {}
        for obj_id in target:
            if obj_id not in survivors:
                commands['%s_list-item' % obj_id] = {'action': 'delete',
                                                     'effects': 'fadeout'}
        return commands

    def rawtext(self):
        rawtext = self.context.getRawText()
        if rawtext:
            return rawtext
        else:
            return "Please enter some text for your page"


class AttachmentView(BaseView):
    attachment_snippet = ZopeTwoPageTemplateFile('attachment.pt')
    create_snippet = ZopeTwoPageTemplateFile('create-att.pt')
    failed_snippet = ZopeTwoPageTemplateFile('failed.pt')
    delete_snippet = ZopeTwoPageTemplateFile('delete-att.pt')

    def attachment_url(self):
        return "%s/@@attachmentSnippet?attachment_id=%s" % (self.context.absolute_url(),
                                                            self.new_attachment().id)

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
            self.errors = {'attachmentFile' : 'You forgot to upload something.'}
            return None 
        
        # Make sure we have a unique file name
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


class ImageManager(WikiEdit, OctopoLite):
    template = ZopeTwoPageTemplateFile("backend-images.pt")
    
    attachment_snippet = ZopeTwoPageTemplateFile('image-manager-image.pt')
    backend_images_snippet = ZopeTwoPageTemplateFile('backend-images.pt')

    def images(self):
        path = '/'.join(self.context.aq_inner.aq_parent.getPhysicalPath())
        image_brains = self.catalog(is_image=True, path=path)
        return image_brains

    def thumb(self):
        image = self.context.aq_inner
        width = height = 100
        
        if not hasattr(image, "thumbnails"):
            image.thumbnails = {}
        size = (width, height)
        if not size in image.thumbnails:
            im = Image.open(StringIO(image.data))
            im.thumbnail(size, Image.ANTIALIAS)
            thumb = StringIO()
            if im.mode != "RGB":
                im = im.convert("RGB")
            im.save(thumb, "JPEG")
            image.thumbnails[size] = thumb.getvalue()

        #fixme: content-type
        return image.thumbnails[size]
    
    def prettySize(self, size):
        if size < 1000:
            return "%d B" % size
        elif size < 1000000:
            return "%.1f" % (int(size / 100) / 10.0) + " kB"
        elif size < 1000000000:
            return "%.1f" % (int(size / 100000) / 10.0) + " mB"
        else:
            return "%.1f" % (int(size / 100000000) / 10.0) + " gB"


    @action('upload-attachment-manager')
    def create_attachment_manager(self, target=None, fields=None):
        new_file = self._handle_createAtt()
        return self.backend_images_snippet()

    
    @action('delete-image')
    def delete_image(self, target=None, fields=None):
        survivors = list(target)
        self.context.manage_delObjects(survivors)
        return self.backend_images_snippet()

    def parse_parent_from(self, brain):
        url = brain.getURL()
        try:
            parent = url.split('/')[-2]
            return parent
        except IndexError:
            return url


class InternalLink(WikiBase):

    def file_list(self):
        path = '/'.join(self.context.aq_inner.aq_parent.getPhysicalPath())
        brains = self.catalog(portal_type='Document',
                              path=path,
                              )
        return [{'url' : brain.getURL(),
          'title' : brain.Title} for brain in brains]


class WikiNewsEditView(WikiEdit):
    """Should look exactly like wiki edit, but also contain description field"""

    def handle_save(self, target=None, fields=None):
        description = self.request.form.get('description', '').strip()
        self.context.setDescription(description)
        return WikiEdit.handle_save(self, target, fields)
