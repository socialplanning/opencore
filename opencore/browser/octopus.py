import sys
import simplejson

def htmlify(js):
    js = simplejson.dumps(js)
    js = js.replace("&", "&amp;")    
    js = js.replace("<", "&lt;")
    js = js.replace(">", "&gt;")
    return '<html><head><meta http-equiv="x-deliverance-no-theme" content="1"/></head><body> %s </body></html>' % js

class Octopus(object):
    """
    Merge of the octopus request form handling with the FormLite form
    delegation code.
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

    def _octopus_allows(self):
        return True

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

        if not self._octopus_allows():
            return "Not allowed"
        
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
