from Products.Five.viewlet.manager import ViewletManagerBase
from zope.component import getMultiAdapter
from zope.interface import implements
from zope.viewlet.interfaces import IViewletManager

def edit_form_manager(view, context=None):
    context = context or view.context
    manager = getMultiAdapter((context,
                               view.request,
                               view),
                              name='opencore.editform')
    assert IEditForm.providedBy(manager)
    return manager

from zope.interface import Interface
class IEditable(Interface):
    """
    Standard interface for editable content.

    Editform views, viewletmanagers, and viewlets should all conform
    to this interface.
    """

    def validate(request):
        """ 
        perform any necessary validation based on the current request
        by iterating through active viewlets.

        returns an error dictionary.
        """

    def save(request):
        """ save state based on the current request. """

class IEditForm(IViewletManager, IEditable):
    """ Viewlet manager for settings you can modify on a piece of content. """

class AddView(object):
    
    #   @@TODO: don't dispatch on REQUEST_METHOD; think about tearing something
    #           out of opencore.browser.formhandler (formlite or the octopus
    #            dispatching) instead?
    def __call__(self):
        if self.request['REQUEST_METHOD'] == 'GET':
            return self.index()
        elif self.request['REQUEST_METHOD'] == 'POST':
            self.POST()
            return self.redirect(self.request)
        # else .. method not supported?

    def POST(self):
        """
        Called when a form is POSTed. This should probably be dispatched 
        on something else, like the form submit button, instead of on the
        request method, but that feels like a detail at this point.
        """
        plugins = edit_form_manager(self)
        request = self.request

        errors = self.validate(request)
        errors.update(plugins.validate(request))
        if errors:
            return self.error_handler(errors)

        object = self.create(request)
        self.save(request, object)

        # now we have a fully created object, so we can pass in 
        # a true context to editforms
        plugins = edit_form_manager(self, context=object)
        plugins.save(request)

    def validate(self, request):
        return IEditable(self.context).validate(request)

    def save(self, request, object):
        IEditable(object).save(request)

    def error_handler(self, errors):
        """
        Takes a dict of errors (key, errortext) and handles them in
        the appropriate way (eg status messages, inline validation,
        etc)
        """
        pass

    def redirect(self, request):
        """
        Issues a client side redirect (which is good behavior for a
        form) at the end of the form handler's actions. Intended to
        be overridden/configured.
        """
        raise NotImplementedError("redirect() should be implemented by a subclass")
    

class EditView(object):
    
    #   @@TODO: don't dispatch on REQUEST_METHOD; think about tearing something
    #           out of opencore.browser.formhandler (formlite or the octopus
    #            dispatching) instead?
    def __call__(self):
        if self.request['REQUEST_METHOD'] == 'GET':
            return self.index()
        elif self.request['REQUEST_METHOD'] == 'POST':
            self.POST()
            return self.redirect(self.request)
        # else .. method not supported?

    def POST(self):
        """
        Called when a form is POSTed. This should probably be dispatched 
        on something else, like the form submit button, instead of on the
        request method, but that feels like a detail at this point.
        """
        plugins = edit_form_manager(self)
        request = self.request

        errors = self.validate(request)
        errors.update(plugins.validate(request))
        if errors:
            return self.error_handler(errors)

        self.save(request)
        plugins.save(request)

    def validate(self, request):
        return IEditable(self.context).validate(request)

    def save(self, request):
        IEditable(self.context).save(request)

    def error_handler(self, errors):
        """
        Takes a dict of errors (key, errortext) and handles them in
        the appropriate way (eg status messages, inline validation,
        etc)
        """
        pass

    def redirect(self, request):
        """
        Issues a client side redirect (which is good behavior for a
        form) at the end of the form handler's actions. Intended to
        be overridden/configured.
        """
        raise NotImplementedError("redirect() should be implemented by a subclass")
    
class NUIEditView(EditView):
    """
    Default base class for NUI-style forms, intended as a conceptual
    refactoring of opencore.nui.browser.base.BaseView and various bits
    of opencore.browser.formhandler
    """

    def redirect(self, request):
        return request.response.redirect(self.context.absolute_url())

    def error_handler(self, errors):
        for key, text in errors:
            self.add_status_message(text)

    def add_status_message(self, text):
        pass

class EditForm(ViewletManagerBase):
    implements(IEditForm)

    def validate(self, request):
        if not hasattr(self, 'viewlets'):
            # is this really necessary?
            self.update()

        errors = {}
        for viewlet in self.viewlets:
            errors.update(viewlet.validate(self.context, request))
        return errors

    def save(self, request):
        if not hasattr(self, 'viewlets'):
            # is this really necessary?
            self.update()

        for viewlet in self.viewlets:
            viewlet.save(self.context, request)

class EditFormViewlet(object):

    def validate(self, context, request):
        return {}

    def save(self, context, request):
        pass
