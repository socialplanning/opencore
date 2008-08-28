from opencore.framework.editform import IEditForm, EditFormViewlet
from zope.interface import implements

class LogoViewlet(EditFormViewlet):

    title = "Logo"
    sort_order = 25

    def save(self, context, request):
        logo = request.get('logo')
        if logo:
            context.setLogo(logo)
    
    def mangled_logo_url(self):
        """When a project logo is changed, the logo_url remains the same.
        This method appends a timestamp to logo_url to trick the browser into
        fetching the new image instead of using the cached one which could be --
        out of date (and always will be in the ajaxy case).
        """
        from DateTime import DateTime
        logo = self.context.getLogo()
        if logo:
            timestamp = str(DateTime()).replace(' ', '_')
            return '%s?%s' % (logo.absolute_url(), timestamp)
        return self.defaultProjLogoURL

    @property
    def logo_html(self):
        macro = self.template.macros['logo']
        from opencore.browser import tal
        return tal.render(macro, tal.make_context(self))

    @action("uploadAndUpdate")
    def change_logo(self, context, request):
        logo = request.form.get("logo")
            
        try:
            self.set_logo()
        except ValueError: # @@ this hides resizing errors
            return

        context.reindexObject('logo')
        return {
            'oc-project-logo' : {
                'html': self.logo_html,
                'action': 'replace',
                'effects': 'highlight'
                }
            }


    @action("remove")
    def remove_logo(self, context, request):
        self.context.setLogo("DELETE_IMAGE")  # blame the AT API
        self.context.reindexObject('logo')
        return {
                'oc-project-logo' : {
                    'html': self.logo_html,
                    'action': 'replace',
                    'effects': 'highlight'
                    }
                }



