"""
Implementation of an OpenPlans-specific page type, based on
RichDocument w/ interface changes and wicked support.
"""
from Products.Archetypes.public import registerType
from Products.Archetypes.public import Schema
from Products.Archetypes.public import BooleanField
from Products.RichDocument.content.richdocument import RichDocument
from Products.RichDocument.widgets.attachments import AttachmentsManagerWidget
from Products.wicked.example.wickeddoc import schema as WickedSchema
from opencore.interfaces import IOpenPage
from Products.OpenPlans.config import PROJECTNAME

from zope.interface import implements

schema = WickedSchema.copy()

hidden_fields = ('relatedItems', 'allowDiscussion')
for fld in hidden_fields:
    schema[fld].widget.visible={'edit': 'invisible',
                                'view': 'invisible',
                                }

schema['text'].scope = 'getContainerPath'
schema['text'].widget.macro = "binsmart_rich"
schema['text'].widget.helper_js = ("toggle_editor.js",)
schema['text'].allowable_content_types = ('text/html',)
schema['text'].default_output_type = 'text/x-html-safe'

schema['description'].widget.rows = 1

schema = schema + Schema((
    BooleanField(
        'displayAttachments',
        default=True,
        languageIndependent=0,
        widget=AttachmentsManagerWidget(
            description="If selected, a list of uploaded attachments will be "
                        "presented at the bottom of the document to allow "
                        "them to be easily downloaded.",
            description_msgid='opencore_help_displayAttachments',
            i18n_domain='opencore',
            label='Display attachments',
            label_msgid='opencore_help_displayAttachments',
            ),
        ),
    ))

class OpenPage(RichDocument):
    """
    OpenPlans page implementation.
    """
    portal_type = meta_type = 'OpenPage'
    archetype_name = 'OpenPage'
    content_icon = 'document_icon.gif'
    typeDescription = 'An OpenPlans wiki page'
    typeDescMsgId = 'OpenPage_description_edit'

    allowed_content_types = ['FileAttachment']

    schema = schema

    implements(IOpenPage)

    def getContainerPath(self):
        path = self.getPhysicalPath()
        return '/'.join(path[:-1])

    def post_validate(self, REQUEST, errors):
        """
        When there is existing binary content in the 'text' field it
        is okay to leave that field blank.
        """
        if errors.has_key('text') and 'required' in errors['text']:
            field = self.getField('text')
            if field.getFilename(self) and field.get_size(self):
                errors.pop('text')

registerType(OpenPage, package=PROJECTNAME)
