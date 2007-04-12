from Products.CMFCore.utils import getToolByName

from zope.app.annotation.interfaces import IAnnotations

from topp.featurelets.interfaces import IFeatureletSupporter
from opencore.featurelets.roster import RosterFeaturelet

def bootstrap_fletmenus(self):
    out = []
    cat = getToolByName(self, 'portal_catalog')
    proj_brains = cat(Type="OpenProject")
    for b in proj_brains:
        proj = b.getObject()

        # clear out any existing menu items
        annotations = IAnnotations(proj)
        menustorage = annotations.get('featurelets_menus')
        if menustorage is not None:
            if menustorage.has_key('featurelets'):
                del menustorage['featurelets']
        
        # set up the proj home menu item
        proj._initProjectHomeMenuItem()

        # check for roster featurelet, remove if yes
        featurelet = RosterFeaturelet()
        supporter = IFeatureletSupporter(proj)
        if featurelet.id in supporter.getInstalledFeatureletIds():
            supporter.removeFeaturelet(featurelet)

        # install roster featurelet
        supporter.installFeaturelet(featurelet)

        out.append("Project '%s' initialized" % proj.getId())

    return '\n'.join(out)
