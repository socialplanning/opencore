==============
 opencore.nui
==============

opencore.nui.base
=================

    >>> from opencore.nui.base import BaseView
    >>> view = BaseView(self.homepage, self.request)
    >>> view.get_portal()
    <PloneSite at /plone>
    
    >>> view.dob_datetime
    DateTime('...')

    >>> view.dob
    'Today'
    
    >>> view.siteURL
    '<URLTool at portal_url>'

    >>> view.sitetitle
    'Portal'
