from opencore.browser.base import BaseView
from opencore.xinha.i18n import xinha_lang_code

class XinhaConfig(BaseView):

    def xinha_lang_code(self):
        return xinha_lang_code(self.request)
