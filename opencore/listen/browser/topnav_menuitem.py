from opencore.browser.topnav.topnav_menuitem import BaseFeatureletMenuItem
from opencore.featurelets.interfaces import IListenFeatureletInstalled

class ListenMenuItem(BaseFeatureletMenuItem):
    name = u'Mailing Lists'
    supp_must_provide = IListenFeatureletInstalled
    item_url = 'lists'
