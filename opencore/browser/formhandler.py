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
    '''Decorator that raises an exception if the request is not POST.'''
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
        try:
            psm_macro = self.main_macros.macros['status-messages']
            status_msg_html = self.render_macro(psm_macro)
            if status_msg_html.strip():
                ret['oc-statusMessage-container'] = {'action': 'replace',
                                                     'html': status_msg_html,
                                                     'effects': 'blink'}
        except AttributeError:
            pass


class FormLite(object):
    """formlike but definitely not formlib; see formlite.txt"""

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
    from pprint import pprint
    globs = locals()
    flags = doctest.ELLIPSIS #| doctest.REPORT_ONLY_FIRST_FAILURE    
    octopolite = doctest.DocFileSuite('octopolite.txt', optionflags=flags)
    formlite = doctest.DocFileSuite('formlite.txt', optionflags=flags,
                                    globs=globs)
    import unittest    
    return unittest.TestSuite((formlite, octopolite))


if __name__ == '__main__':
    import unittest
    unittest.TextTestRunner().run(test_suite())
