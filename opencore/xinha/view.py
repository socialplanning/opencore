from opencore.browser.base import BaseView
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from opencore.xinha.i18n import xinha_lang_code

class XinhaConfig(BaseView):
    template92 = ZopeTwoPageTemplateFile("xinha-092.pt")
    template96 = ZopeTwoPageTemplateFile("xinha-096.pt")

    def xinha_lang_code(self):
        xinha_lang_dir = None
        if self.use_new():
            xinha_lang_dir = "thirdparty/xinha96r1270/lang"
        return xinha_lang_code(self.request, 
                               xinha_lang_dir)

    def __call__(self):
        if self.use_new():
            return self.template96()
        return self.template92()

    def use_new(self):
        member = self.loggedinmember
        if member is None:
            return False

        opt_ins = get_config('xinha_upgrade_optins', '').split()
        opt_ins = [x.strip() for x in opt_ins if x.strip()]

        if member.getId() in opt_ins:
            return True
        return False
