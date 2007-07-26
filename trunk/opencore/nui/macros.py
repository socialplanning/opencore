from Products.Five import BrowserView
from Products.Five.skin.standardmacros import StandardMacros as BaseMacros
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile


class NuiMacros(BrowserView):
    """ """
    template = ZopeTwoPageTemplateFile('main_template.pt')

    def __getitem__(self, key):
        return self.template.macros[key]


class StandardMacros(BaseMacros):
    macro_pages = ('nui_macros',
                   'five_template',
                   'standard_macros',
                   'nui_batch_macros')
