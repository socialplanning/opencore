from Products.CMFCore.utils import getToolByName

from zope.interface import alsoProvides

from opencore.siteui.interfaces import IMemberFolder
from opencore.siteui.interfaces import IMemberHomePage



def mark_member_homes(self):
    out = []
    mtool = getToolByName(self, 'portal_membership')
    pfolder = mtool.getMembersFolder()
    mem_folders = pfolder.objectValues(spec='ATFolder')
    for mem_folder in mem_folders:
        alsoProvides(mem_folder, IMemberFolder)

        mem_home_id = mem_folder.getDefaultPage()
        if mem_home_id is not None:
            mem_home = mem_folder._getOb(mem_home_id)
            alsoProvides(mem_home, IMemberHomePage)
            mem_home.setLayout('profile.html')

        out.append("marked for %s" % mem_folder.getId())

    return '\n'.join(out)
