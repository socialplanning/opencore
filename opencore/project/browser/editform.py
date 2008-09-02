from opencore.framework.editform import IEditForm, EditFormViewlet
from zope.interface import implements

class LogoViewlet(EditFormViewlet):

    title = "Logo"
    sort_order = 25

    defaultProjLogoURL = '++resource++img/default-projlogo.gif'

    def save(self, context, request):
        if request.form.get('task|oc-project-logo|uploadAndUpdate'):
            self.change_logo(context, request)
        elif request.form.get('task|oc-project-logo|remove'):
            self.remove_logo(context, request)
        else:
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

    def logo_html(self):
        macro = self.template.macros['logo']
        from opencore.browser import tal
        return tal.render(macro, tal.make_context(self))


    def change_logo(self, context, request):
        logo = request.form.get("logo")
            
        try:
            context.setLogo(logo)
        except ValueError: # @@ this hides resizing errors
            return

        context.reindexObject('logo')
        return {
            'oc-project-logo' : {
                'html': self.logo_html(),
                'action': 'replace',
                'effects': 'highlight'
                }
            }

    def remove_logo(self, context, request):
        self.context.setLogo("DELETE_IMAGE")  # blame the AT API
        self.context.reindexObject('logo')
        return {
                'oc-project-logo' : {
                    'html': self.logo_html(),
                    'action': 'replace',
                    'effects': 'highlight'
                    }
                }

from opencore.interfaces import IHomePage
class HomepageViewlet(EditFormViewlet):

    title = "Home page"
    sort_order = 35

    def save(self, context, request):
        home_page = request.form.get('home-page')
        hpcontext = IHomePage(context)
        if home_page is not None:
            if hpcontext.home_page != home_page:
                hp_url = '/'.join((context.absolute_url(), home_page))
                hpcontext.home_page = home_page

        return IHomePage(self.context).home_page

    def homepages(self):
        """possible homepages for the app"""        

        from opencore.project.browser.home_page import IHomePageable
        from zope.component import subscribers

        homepages = subscribers((self.context,), IHomePageable)

        homepage_data = []

        for homepage in homepages:
            checked = False
            if IHomePage(self.context).home_page == homepage.url:
                checked = True

            homepage_data.append(dict(id=homepage.id,
                                  title=homepage.title,
                                  url=homepage.url,
                                  checked=checked))
        return homepage_data

