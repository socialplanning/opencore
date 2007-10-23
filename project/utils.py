from topp.featurelets.interfaces import IFeatureletSupporter

def get_featurelets(project):
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
