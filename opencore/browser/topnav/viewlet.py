from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from Products.Five.viewlet.viewlet import ViewletBase

class BaseMenuItem(ViewletBase):
    render = ZopeTwoPageTemplateFile('menuitem.pt')
