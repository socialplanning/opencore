# @@ investigate adding other ztc etc factories here

def layer_decorator(func):
    def wrapped(*args, **kwargs):
        layer = kwargs.get('layer')
        if layer:
            del kwargs['layer']
        suite = func(*args, **kwargs)
        if layer:
            suite.layer = layer
        return suite
    wrapped.__name__ = func.__name__
    return wrapped

def decorated_factories():
    from Testing.ZopeTestCase.zopedoctest.functional import *
    factories = locals().items()
    factories = [(name, layer_decorator(f)) for name, f in factories]
    globs = globals()
    globs.update(dict(factories))

decorated_factories()

__all__ = [
    'ZopeDocTestSuite',
    'ZopeDocFileSuite',
    'FunctionalDocTestSuite',
    'FunctionalDocFileSuite',
    ]
