from opencore.browser.base import BaseView
from opencore.configuration import OC_REQ
import pkg_resources as pkr


class OpencoreVersionView(BaseView):

    def version_data(self, group='opencore.versions'):
        comp_data = []
        for ep in pkr.iter_entry_points(group):
            req = ep.name
            dist = pkr.get_distribution(req)
            version = dist.version
            comp_data.append(dict(component=req, version=version))
        return comp_data
