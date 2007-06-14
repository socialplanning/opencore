"""Decorators for working with form submission"""

from zExceptions import Forbidden

def button(name=None):
    def curry(handle_request):
        def new_method(self):
            if self.request.get(name):
                return handle_request(self)
            return None
        return new_method
    return curry


def post_only(raise_=True):
    def inner_post_only(func):
        """usually wrapped by a button"""
        def new_method(self):
            if self.request.environ['REQUEST_METHOD'] == 'GET':
                if raise_:
                    raise Forbidden('GET is not allowed here')
                return
            return func(self)
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
        # XXX todo don't rely on underscore special character
        target, action = self.request.form.get("task").split("_")

        if target == 'batch' and self.request.form.get('batch[]'):
            target = self.request.form.get("batch[]")
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
    """undo the octopization for zope"""
    def inner(self, action, target, fields):
        octo_form = self.request.form.copy()
        ret = {}
        for t, f in zip(target, fields):
            self.request.form = f.copy()
            ret[t] = func(self)
        self.request.form = octo_form
        return ret
    return inner
