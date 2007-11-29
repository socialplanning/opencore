from opencore.browser.base import BaseView
import pkg_resources

class OpencoreVersionView(BaseView):

    components = 'opencore topp.utils topp.featurelets oc-js'.split()

    def version_data(self):
        get_dist = pkg_resources.get_distribution
        create_req = pkg_resources.Requirement.parse

        comp_data = []
        for comp in self.components:
            try:
                req = create_req(comp)
                dist = get_dist(req)
            except (ValueError, pkg_resources.DistributionNotFound):
                version = 'Component not found'
            else:
                version = dist.version
            comp_data.append(dict(component=comp, version=version))

        return comp_data
