from opencore.browser.topnav.topnav_menuitem import BaseFeatureletMenuItem
from opencore.wordpress.interfaces import IWordPressFeatureletInstalled

class WordpressMenuItem(BaseFeatureletMenuItem):
    name = u'Blog'
    supp_must_provide = IWordPressFeatureletInstalled
    item_url = 'blog'
