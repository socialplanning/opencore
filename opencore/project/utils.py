from opencore.utility.interfaces import IProvideSiteConfig
from topp.featurelets.interfaces import IFeatureletSupporter
from zope.component import getUtility, ComponentLookupError

def get_featurelets(project):
    """
    Returns a list of dicts representing the featurelets that are
    installed into the provided project.
    """
    supporter = IFeatureletSupporter(project)
    flet_ids = supporter.getInstalledFeatureletIds()
    getfletdesc = supporter.getFeatureletDescriptor
    result = []
    for id in flet_ids:
        flet_info = getfletdesc(id)
        if flet_info is None:
            # flet registered but non-functional
            continue
        menu_item = flet_info['menu_items'][0]
        result.append(
            {'name': id,
             'url' : menu_item['action'],
             'title': menu_item['title'],
             }
            )
    return result

_project_noun = None
def project_noun():
    """Returns our global config's projtxt setting, which should be
    used everywhere we refer to 'projects'.
    """
    global _project_noun
    if _project_noun:
        return _project_noun
    default = 'project'
    try:
        config = getUtility(IProvideSiteConfig)
    except ComponentLookupError:
        # Ugh. This happens during import time, it's used by a couple
        # of archetypes schema labels.  Lookup fails because we
        # haven't yet loaded the zcml that creates an implementation
        # of IProvideSiteConfig.  We have no choice but to return the
        # default; I'm hoping this is OK because we don't actually
        # care about archetypes labels.  - PMW
        return default
    _project_noun = config.get('projtxt', default=default)
    return _project_noun

def project_path(proj_id=None):
    """
    Returns the specified project's home folder path relative to the
    site root.
    """
    # XXX this function should go away.
    import warnings
    warnings.warn(DeprecationWarning(
        "project_path should go away; either use BaseView.project_url() or... "
        "um... some traversal api we need to create"))
    projects_url= project_noun() + 's'
    if proj_id is None:
        return projects_url
    return "%s/%s" % (projects_url, proj_id)
