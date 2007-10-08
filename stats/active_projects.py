From Products.CMFCore.utils import getToolByName
import DateTime

# does it count private projects?
# "active" is defined as having been modified in the last 30 days
def get_active_projects():    
    catalog = getToolByName(app.openplans, 'portal_catalog')
    query = dict(portal_type='OpenProject')
    brains = catalog(**query)

    filtered_brains = [brain for brain in brains if brain.modified > DateTime.now()-30]

    return filtered_brains


if __name__ == "__main__":
    a_projects = get_active_projects()
    print len(a_projects)
