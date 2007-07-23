from cStringIO import StringIO
from os.path import join, abspath, dirname, basename
import time

import ZConfig
from ZODB.POSException import ConflictError

from Products.CMFCore.utils import getToolByName
from Products.Archetypes.Extensions.utils import install_subskin

from Products.OpenPlans.config import GLOBALS

VOCAB_PREFIX = abspath(join(dirname(__file__), '..', 'vocabulary'))
CONF_PREFIX = abspath(join(dirname(__file__), '..', 'conf'))

def vocab_file(file): return join(VOCAB_PREFIX, file)

def conf_file(file): return join(CONF_PREFIX, file)

def register(portal, pkg):
    qi = portal.portal_quickinstaller
    if not qi.isProductInstalled(pkg):
	qi.installProduct(pkg)
	
def requires(portal, pkg):
    """Make sure that we can load and install the package into the
    site"""
    register(portal, pkg)

def optional(portal, pkg):
    try:
        register(portal, pkg)
        return True
    except ConflictError:
        raise
    except:
        return False

def parseDepends():
    schema = ZConfig.loadSchema(conf_file('depends.xml'))
    config, handler = ZConfig.loadConfig(schema,
                                         conf_file('depends.conf'))
    return config, handler

def installDepends(portal):
    config, handler = parseDepends()
    # Curry up some handlers
    def required_handler(values, portal=portal):
        for pkg in values:
            requires(portal, pkg)

    def optional_handler(values, portal=portal):
        for pkg in values:
	    optional(portal, pkg)

    handler({'required' : required_handler,
             'optional' : optional_handler,
             })

kupu_libraries = [
    dict(icon='string:${portal_url}/openproject_icon.png',
         id='projects',
         src='string:${portal/projects/absolute_url}/kupucollection.xml',
         title='string:Projects',
         uri='string:${portal/projects/absolute_url}'),

    dict(icon='string:${portal_url}/openproject_icon.png',
         id='current',
         src='string:${folder_url}/../kupucollection.xml',
         title='string:Current Folder',
         uri='string:${folder_url}/..'),
    
    dict(icon='string:${portal_url}/group.gif',
         id='people',
         title='string:People'),
    
    dict(icon='string:${portal_url}/kupuimages/confirm_icon.gif',
         id='myitems',
         src='string:${portal_url}/kupumyitems.xml',
         title='string:My items',
         uri='string:${portal_url}/kupumyitems.xml'),
    
    dict(icon='string:${portal_url}/kupuimages/confirm_icon.gif',
         id='recentitems',
         src='string:${portal_url}/kupurecentitems.xml',
         title='string:Recent',
         uri='string:${portal_url}/kupurecentitems.xml')]

kupu_resource_map = dict(linkable=('Document',
                              'Image',
                              'File',
                              'News Item',
                              'Event',
                              'PoiIssue',
                              'PoiResponse',
                              ),
                    mediaobject=('Image',),
                    collection=('Plone Site',
                                'Folder',
                                'OpenProject',
                                'Poitracker',
                                'Large Plone Folder'))

def setupKupu(portal, out):
    # this should really read from a config file
    # but for now, will do
    # this code taken from kupu source(plone config example)
    
    mt = getToolByName(portal, 'portal_membership')
    people = 'portal/%s/absolute_url' %mt.getMembersFolder().getId()

    people = dict(src='string:${%s}/kupucollection.xml' %people,
                  uri='string:${%s}' %people)
    [kl.update(people) for kl in kupu_libraries \
     if kl['id'] == 'people']

    typetool = getToolByName(portal, 'portal_types')
    def typefilter(types):
        all_meta_types = dict([ (t.id, 1) for t in typetool.listTypeInfo()])
        return [ t for t in types if t in all_meta_types ]
        
    kupu = getToolByName(portal, 'kupu_library_tool')
    libs = kupu.zmi_get_libraries()
    kupu.deleteLibraries(range(len(libs)))

    types = kupu.zmi_get_type_mapping()
    kupu.deleteResourceTypes([ t for (t,p) in types])

    for k,v in kupu_resource_map.items():
        kupu.addResourceType(k, typefilter(v))

    for lib in kupu_libraries:
        kupu.addLibrary(**lib)
        
    kupu.zmi_set_default_library('myitems')
    
    if out:
        print >> out, "Kupu setup completed"

def reinstallSubskins(portal):
    out = StringIO()
    stool = getToolByName(portal, 'portal_skins')
    dels = [id for id in stool.objectIds() if id.startswith('openplans')]
    stool.manage_delObjects(ids=dels)
    install_subskin(portal, out, GLOBALS)
