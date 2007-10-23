from Products.Five import BrowserView
from Products.Five.skin.standardmacros import StandardMacros as BaseMacros
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile

class WikiMacros(BaseMacros):
    macro_pages = ('wiki_macros',)
