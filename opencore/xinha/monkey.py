""" 
see openplans:#2792
I'd REALLY like to be able to remove all of this,
hopefully there can be an upstream fix
 """

#from zope.publisher.interfaces.browser import IBrowserPublisher
#class IResourceDirWithLangResource(IBrowserPublisher):
#    pass

from Products.Five.browser.metaconfigure import resourceDirectory as superdirective
from Products.Five.browser.resource import DirectoryResourceFactory as superfactory
from Products.Five.browser.resource import DirectoryResource as superclass

from zope import interface
_marker = object()
class DirectoryResource(superclass):
    #interface.implements(IResourceDirWithLangResource)

    @property
    def lang(self):
        return self['lang']

    def get(self, name, default=_marker):
        original_resource = superfactory.resource
        superfactory.resource = DirectoryResource
        try:
            return superclass.get(self, name, default)
        finally:
            superfactory.resource = original_resource

from zope.app.publisher.browser.metadirectives import IResourceDirectoryDirective as superiface
from zope.configuration.fields import GlobalObject
from zope.schema import BytesLine
class IResourceDirectoryDirective(superiface):
    package = GlobalObject(
        title=u"The package name to serve resources from",
        description=u"""\
          This is the name of the package containing the resource
          directory being registered. If this is not provided, the
          ZCML context's path is assumed as the directory prefix.
          """,
        required=False,
        )
    directory = BytesLine(
        title=u"Directory",
        description=u"The directory containing the resource data.",
        required=True
        )

from pkg_resources import resource_filename
def resourceDirectory(_context, name, directory, package=None,
                      layer=None, permission='zope.Public'):
    if package is not None:
        directory = resource_filename(package.__name__, directory)
    else:
        directory = _context.path(directory)

    original_resource = superfactory.resource
    superfactory.resource = DirectoryResource
    try:
        superdirective(_context, name, directory, permission=permission)
    finally:
        superfactory.resource = original_resource
