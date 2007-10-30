from zope.app.form.browser import ASCIIWidget
from zope.app.form.browser.widget import renderTag

from config import LIST_SUFFIX as SUFFIX

class OpenListNameWidget(ASCIIWidget):
    """
    Doesn't change behaviour, just causes the mailing list suffix
    (i.e. the FQDN of the list address) to be displayed after the
    input box.
    """
    def __call__(self):
        value = self._getFormValue()
        if value.endswith(SUFFIX):
            value = value[:-len(SUFFIX)]
        return renderElement(self.tag,
                             type=self.type,
                             name=self.name,
                             id=self.name,
                             value=value,
                             cssClass=self.cssClass,
                             extra=self.extra)

def renderElement(tag, **kw):
    contents = kw.pop('contents', None)
    if contents is not None:
        # Do not quote contents, since it often contains generated HTML.
        return u"%s>%s</%s> %s" % (renderTag(tag, **kw), contents, tag,
                                   SUFFIX)
    else:
        return renderTag(tag, **kw) + " />" + SUFFIX
