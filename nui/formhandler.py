"""Decorators for working with form submission"""
import sys
from zExceptions import Forbidden

def button(name=None):
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
    def inner_anon_only(func):
        def new_method(self, *args, **kw):
            redirect_path = redirect_to
            if not redirect_path:
                redirect_path = self.came_from
            if self.loggedin:
                return self.redirect(redirect_path)
            return func(self, *args, **kw)
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
    documented in opencore.nui.project/contents.txt
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

def dict_to_json(func):
    """
    this is as dumb as it can possibly be
    """
    def inner(*args, **kw):
        val = func(*args, **kw)
        if not isinstance(val, dict):
            return val
        return "{%s}" % ', '.join(["%s:'%s'" % (k,v) for k,v in val.items()])
    return inner

class OctopoLite(object):

    no_postprocess = False

    def __call__(self, *args, **kw):
        raise_ = kw.pop('raise_', False)  #sorry
        try:
            action, objects, fields = self.__preprocess()
        except:
            action, objects, fields = (None, [], {})
        ret = self.__delegate(action, objects, fields, raise_)
        if not no_postprocess:
            return self.__postprocess(ret)
        return ret

    def __preprocess(self):
        """ yanked from octopus """
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
        
        return (action, target, fields)

    def __delegate(self, action, objects, fields, raise_=False):
        """ yanked from FormLite """
        if action in self.actions:
            return self.actions[action](self, objects, fields)
        elif raise_:
            raise KeyError("No actions in request")
        elif self.actions.default is not None:
            self.no_postprocess = True
            return self.actions.default(self, objects, fields)
        else:
            return None

    def __postprocess(self, val):
        """ yanked from octopus """
        mode = self.request.form.get("mode")
        if mode == "async":
            return ret

        return self.redirect(self.request.environ['HTTP_REFERER'])
    
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

class Actions(dict):
    """ functions registry """
    __repr__ = dict.__repr__
    def __init__(self):
        dict.__init__(self)
        self.default = None

class Action(object):

    def __init__(self, name, apply=None, **options):
        self.name = name
        self.options = options
        self.apply = apply

    def __call__(self, view, *args, **kw):
        method = getattr(view, self.name)
        options = dict(self.options, **kw)
        if not self.apply:
            return method(*args, **options)
        newmethod = method.im_func  # decorate an unbound method
        for decorator in self.apply:
            newmethod = decorator(newmethod)
        newmethod.__name__ = method.__name__
        return newmethod(view, **options)  # our method is now unbound

class action(object):
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
    
import os, sys, unittest, doctest
from zope.testing import doctest

flags = doctest.ELLIPSIS | doctest.REPORT_ONLY_FIRST_FAILURE

def test_suite():
    return doctest.DocFileSuite('formlite.txt', optionflags=flags)

if __name__ == '__main__':
    unittest.TextTestRunner().run(test_suite())
