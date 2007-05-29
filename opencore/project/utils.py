from topp.featurelets.interfaces import IFeatureletSupporter

def get_featurelets(project):
    supporter = IFeatureletSupporter(project)
    flet_ids = supporter.getInstalledFeatureletIds()
    getfletdesc = supporter.getFeatureletDescriptor
    flets = [{'name': id,
              'url' : getfletdesc(id)['content'][0]['id']}
             for id in flet_ids]
    return flets
