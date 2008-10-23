"""Decorators for working with form submission"""

import logging
import simplejson
import sys
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
    # XXX should this do the __name__ mangling for use with @action?
    def inner_post_only(func):
        """usually wrapped by a button"""
        def new_method(self, *args, **kw):
            if self.request.environ['REQUEST_METHOD'] == 'GET':
                # XXX errr. that's not exactly the condition our name suggests.
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
    # XXX should this do the __name__ mangling for use with @action?
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


def htmlify(js):
    '''Convert python types to JSON and wrap that in an html body.
    '''
    js = simplejson.dumps(js)
    js = js.replace("&", "&amp;")    
    js = js.replace("<", "&lt;")
    js = js.replace(">", "&gt;")
    return '<html><head><meta http-equiv="x-deliverance-no-theme" content="1"/></head><body> %s </body></html>' % js



class Actions(dict):
    """ functions registry for use by the @action decorator"""
    __repr__ = dict.__repr__
    def __init__(self):
        dict.__init__(self)
        self.default = None

class Action(object):
    '''function wrapper used by the @action decorator '''
    def __init__(self, name, apply=None, **options):
        self.name = name
        self.options = options
        self.apply = apply

    def __call__(self, instance_, *args, **kw):
        method = getattr(instance_, self.name)
        options = dict(self.options, **kw)
        if not self.apply:
            return method(*args, **options)
        newmethod = method.im_func  # decorate an unbound method
        for decorator in self.apply:
            newmethod = decorator(newmethod)
        newmethod.__name__ = method.__name__
        return newmethod(instance_, **options)  # our method is now unbound

class action(object):
    '''Decorator that wraps the decorated method as an Action,
    and adds it to an Actions mapping for later dispatching.'''
    # modfied from zope.formlib (ZPL)
    def __init__(self, label, default=False, 
                 actions=None, apply=None,
                 **options):
        caller_locals = sys._getframe(1).f_locals
        if actions is None:
            actions = caller_locals.get('actions')
        if actions is None:
            actions = caller_locals['actions'] = Actions()
        self.actions = actions
        self.label = label
        self.options = options
        if default:
            if actions.default is not None:
                raise Exception("Only one default action is permitted per action registry")
        self.default = default
        if isinstance(apply, tuple):
            self.apply = apply
        elif callable(apply):
            self.apply = (apply,)
        elif apply is None:
            self.apply = None
        else:
            raise Exception("apply must be either a function or a tuple of functions")

    def __call__(self, func):
        a = Action(func.__name__, apply=self.apply, **self.options)
        self.actions[self.label] = a
        if self.default:
            self.actions.default = a
        return func



class Octopus(object):
    """
    Request form handling, using action delegation via the @action
    decorator.

    Not tied to any framework - just needs a dict to be returned by
    self._octopus_request() and HTML from self._octopus_template().
    """

    def _octopus_get(self, key):
        """
        Fetch value 'key' from the request. Must be implemented by a
        subclass, since it is framework-dependent.

        Return request value if it exists, otherwise None.
        """
        pass
    
    def _octopus_request(self):
        """
        Return entire request content as a dictionary. Must be implemented
        by a subclass, since it is framework-dependent.
        """
        pass

    def _octopus_template(self):
        """
        Return a rendered template for synchronous requests. Must be
        implemented by a subclass.
        """
        pass

    def _octopus_async_postprocess(self, ret):
        """
        A hook for subclasses to modify the return value or perform
        other application-specific logic on asynchronous requests.
        """
        pass

    def __call__(self, *args, **kw):
        """
        drives the request process through the following steps:

        1. parsing the request form to determine the action
           and (optionally) targets and fields

        2. triggering delegation to the correct action method
           decorated with @action

        3. returning either a rendered template (if the request is
           synchronous) or a dictionary of info to be passed back to
           the browser (if the request is async).
        """
        raise_ = kw.pop('raise_', False)  #sorry
        try:
            action, objects, fields = self.__preprocess()
        except:
            action, objects, fields = (None, [], [])

        ret = self.__delegate(action, objects, fields, raise_)
        if ret is None:
            ret = dict()

        mode = self._octopus_get('mode')
        if mode == 'async':
            self._octopus_async_postprocess(ret)
            return htmlify(ret)  # no
        else:
            return self._octopus_template()

    def __preprocess(self):
        """
        yanked from octopus IE crap means we need to encode task in
        the key, not the value. so format will be task:$TARGET:$ACTION
        """
        task = None
        request = self._octopus_request()
        for key in request.keys():
            key = key.split("|")
            if len(key) > 1 and key[0] == "task":
                task = key[1:]
                break

        if not task:
            return (None, [], [])
        
        if len(task) == 1:
            return (task[0], [], [])

        target, action = task[0], task[1]

        if target.startswith('batch_'):
            target_elem = target.split('_')[1]
            target = self._octopus_get(target_elem)
            if target is None:
                target = []
        if not isinstance(target, (tuple, list)):
            target = [target]

        # grab items' fields from request and fill dicts in an ordered list
        fields = []
        for item in target:
            itemdict = {}
            filterby = item + '_'
            keys = [key for key in self._octopus_request()
                    if key.startswith(filterby)]
            for key in keys:
                itemdict[key.replace(filterby, '')] = self._octopus_get(key)
            fields.append(itemdict)
        
        return (action, target, fields)

    def __delegate(self, action, objects, fields, raise_=False):
        """ delegate to the appropriate action method, if it exists."""
        
        #check self and superclasses for appropriate action methods
        bases = [self.__class__]
        while bases:
            base = bases[0]
            if hasattr(base, 'actions'):
                try:
                    if action in base.actions:
                        return base.actions[action](self, objects, fields)
                except TypeError: #actions isn't a list
                    pass

            bases = bases[1:]
            bases += list(base.__bases__)

        if raise_:
            raise KeyError("No actions in request")
        elif self.actions.default is not None:
            return self.actions.default(self, objects, fields)


class OctopoLite(Octopus):
    """
    Implements action dispatch and Octopus and request form handling
    with opencore.  Meant to be used as a mix-in to any class that
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


def test_suite():
    from pprint import pprint
    globs = locals()
    from zope.testing import doctest
    flags = doctest.ELLIPSIS #| doctest.REPORT_ONLY_FIRST_FAILURE    
    octopolite = doctest.DocFileSuite('octopolite.txt', optionflags=flags,
                                      globs=globs)
    import unittest
    return unittest.TestSuite((octopolite,))


if __name__ == '__main__':
    import unittest
    unittest.TextTestRunner().run(test_suite())
