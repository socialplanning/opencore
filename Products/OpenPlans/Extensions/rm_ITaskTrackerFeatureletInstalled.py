from opencore.featurelets.interfaces import ITaskTrackerFeatureletInstalled
from Products.Five.utilities.marker import erase as noLongerProvides
from StringIO import StringIO

def rm_ITaskTrackerFeatureletInstalled(self):
    """extension method where self is the portal"""
    projs_with_marks_removed = []
    projs_with_no_mark = []

    for pbrain in self.portal_catalog(portal_type='OpenProject'):
        proj = pbrain.getObject()
        if ITaskTrackerFeatureletInstalled.providedBy(proj):
            noLongerProvides(proj, ITaskTrackerFeatureletInstalled)
            projs_with_marks_removed.append(proj.id)
        else:
            projs_with_no_mark.append(proj.id)

    out = StringIO()
    out.write('Projects with no markings:\n')
    out.write('\n'.join(projs_with_no_mark))
    out.write('\n\n')
    out.write('Projects with marking removed:\n')
    out.write('\n'.join(projs_with_marks_removed))
    return out.getvalue()
