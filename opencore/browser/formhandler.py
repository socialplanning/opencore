"""Decorators for working with form submission"""

import logging
import opencore.browser.octopus

# pw: dunno why, but lots of things import action from here instead of
# from browser.octopus.
from opencore.browser.octopus import action
from zExceptions import Forbidden

log = logging.getLogger('opencore.browser.formhandler')

def button(name):
    def curry(handle_request):
        def new_method(self):
            if self.request.form.get(name):
                return handle_request(self)
            return None
        return new_method
    return curry


def post_only(raise_=True):
    def inner_post_only(func):
        """usually wrapped by a button"""
        def new_method(self, *args, **kw):
            if self.request.environ['REQUEST_METHOD'] == 'GET':
                if raise_:
                    raise Forbidden('GET is not allowed here')
                return
            return func(self, *args, **kw)
        return new_method
    return inner_post_only


def anon_only(redirect_to=None):
    """Redirect if the user is logged in.  For use decorating methods
    of BaseView or subclasses.

    redirect_to, if provided, is expected to be a method or attribute
    of the class.

    The class must also provide these attributes:
    * loggedin (bool)
    * redirect(), method taking a str
    * came_from (str), used as fallback if redirect_to not provided or false.
    """
    def inner_anon_only(func):
        def new_method(self, *args, **kw):
            if not self.loggedin:
                return func(self, *args, **kw)
            else:
                if isinstance(redirect_to, property):
                    redirect_path = redirect_to.fget
                else:
                    redirect_path = redirect_to
                if callable(redirect_path):
                    redirect_path = redirect_path(self)
                if not redirect_path:
                    redirect_path = self.came_from
                return self.redirect(redirect_path)
        return new_method
    return inner_anon_only


def octopus(func):
    """
    A (hopefully) generic decorator to handle complex forms with
    multiple actions and multiple items which can be acted upon
    either singly or in a batch, with the call made either 
    asynchronously or synchronously with javascript disabled.

    This method expects to decorate a method which takes, in order,
      * an action to apply (a unique identifier for a method to
                            delegate to or an action to perform),
      * a list of targets (unique identifiers for items to act upon),
      * a list of fields (a dict of fieldname:values to apply to the
                          targets, in the same order as the targets)

    It expects to be returned a value to be sent, unmodified, directly
    to the client in the case of an AJAX request.

    It expects a very specific format for the request; this is 
    documented in opencore.project.browser/contents.txt
    """
    def inner(self):
        # XXX todo don't rely on '_' or ':' special characters
        target, action = self.request.form.get("task").split("_")

        if target.startswith('batch:'):
            target_elem = target.split(':')[1]
            target = self.request.form.get(target_elem)
            if target is None:
                target = []
        if not isinstance(target, (tuple, list)):
            target = [target]

        # grab items' fields from request and fill dicts in an ordered list
        fields = []
        for item in target:
            itemdict = {}
            filterby = item + '_'
            keys = [key for key in self.request.form if key.startswith(filterby)]
            for key in keys:
                itemdict[key.replace(filterby, '')] = self.request.form.get(key)
            fields.append(itemdict)

        ret = func(self, action, target, fields)
        mode = self.request.form.get("mode")

        if mode == "async":
            self.response.setHeader('Content-Type', "application/javascript;charset=utf-8")
            return ret
        return self.redirect(self.request.environ['HTTP_REFERER'])

    return inner

def deoctopize(func):
    """
    A decorator to reformat an octopized request to match zope's conventions.
    Intended to be decorated by octopus.

    Constructs a zope-style request for each item in the target list and calls
    the decorated function with that request per item, and constructs a JSONish
    return value to match the format expected by the javascript based on the action.

    Passes in an extra request field, 'octopus-item', with the id of the item being
    acted upon, so that the decorated function has the necessary information about 
    what item to act upon. This can, of course, be ignored entirely.
    """
    def inner(self, action, target, fields):
        octo_form = self.request.form.copy()
        if action == 'delete':
            ret = []
        elif action == 'update':
            ret = {}
        for t, f in zip(target, fields):
            form = f.copy()
            form['octopus-item'] = t
            self.request.form = form
            tret = func(self)
            if action == 'delete':
                if tret:
                    ret.append[target]
            elif action == 'update':
                ret[t] = tret
        self.request.form = octo_form
        return ret
    return inner

class OctopoLite(opencore.browser.octopus.Octopus):
    """
    Merge of the octopus request form handling with the FormLite form
    delegation code.  Meant to be used as a mix-in to any class that
    also subclasses opencore.browser.base.BaseView.
    """

    def _octopus_get(self, key):
        return self.request.form.get(key)

    def _octopus_request(self):
        return self.request.form

    def _octopus_template(self):
        """
        Returns either the rendered template attribute, or None if the
        self.template is None.
        """
        if getattr(self, 'template', None) is not None:
            return self.template()
        if getattr(self, 'index', None) is not None:
            return self.index()

    def _octopus_async_postprocess(self, ret):
        #self.response.setHeader('Content-Type', "application/javascript;charset=utf-8")
        try:
            psm_macro = self.main_macros.macros['status-messages']
            status_msg_html = self.render_macro(psm_macro)
            ret['oc-statusMessage-container'] = {'action': 'replace',
                                                 'html': status_msg_html,
                                                 'effects': 'blink'}
        except AttributeError:
            pass

#    def _octopus_allows(self):
#        oreq = self._octopus_request()
#        if oreq.has_key('-C'):
#            return True #we allow all non-editing requests
#
#        auth = self.get_tool('browser_id_manager').getBrowserId()
#        log.debug("authenticators:", self._octopus_get('authenticator'),
#                  auth)
#        #return self._octopus_get('authenticator') == auth
#        return True
        
# XXX remove as unused
class FormLite(object):
    """formlike but definitely not formlib"""

    def handle_request(self, raise_=False):
        for key in self.actions:
            if self.request.form.has_key(key):
                return self.actions[key](self)
        if raise_:
            raise KeyError("No actions in request")
        if self.actions.default is not None:
            return self.actions.default(self)

    


def test_suite():
    from zope.testing import doctest
    flags = doctest.ELLIPSIS | doctest.REPORT_ONLY_FIRST_FAILURE
    return doctest.DocFileSuite('octopolite.txt', optionflags=flags)

if __name__ == '__main__':
    import unittest
    unittest.TextTestRunner().run(test_suite())
