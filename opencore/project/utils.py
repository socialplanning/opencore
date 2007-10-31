from topp.featurelets.interfaces import IFeatureletSupporter

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
        menu_item = flet_info['menu_items'][0]
        result.append(
            {'name': id,
             'url' : menu_item['action'],
             'title': menu_item['title'],
             }
            )
    return result

def project_path(proj_id):
    """
    Returns the specified project's home folder path relative to the
    site root.
    """
    return "projects/%s" % proj_id
