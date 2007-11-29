from opencore.browser.base import BaseView
from opencore.configuration import OC_REQ
import pkg_resources as pkr


class OpencoreVersionView(BaseView):

    def required_version_data(self):
        comp_data = []
        dist = pkr.get_distribution(OC_REQ)
        for name in dist.dists_we_care_about:
            req = pkr.Requirement.parse(name)
            dist = pkr.get_distribution(req)
            version = dist.version
            comp_data.append(dict(component=name, version=version))
        return comp_data
    
    def version_data(self, group='opencore.versions'):
        comp_data = []
        for ep in pkr.iter_entry_points(group):
            req = ep.load()
            dist = pkr.get_distribution(req)
            version = dist.version
            comp_data.append(dict(component=ep.name, version=version))
        return comp_data
