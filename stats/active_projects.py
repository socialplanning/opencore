from Products.CMFCore.utils import getToolByName
import DateTime

# run this file with zopectl> run [filename]

# "active" is defined as having been modified in the last 30 days
# both public and private projects are counted
def get_active_projects():    
    catalog = getToolByName(app.openplans, 'portal_catalog')
    query = dict(portal_type='OpenProject')
    brains = catalog(**query)

    filtered_brains = [brain for brain in brains if brain.modified > DateTime.now()-.1]

    return filtered_brains


if __name__ == "__main__":

    # change to the admin user
    username = 'admin'
    from AccessControl.SecurityManagement import newSecurityManager
    user = app.acl_users.getUser(username)
    user = user.__of__(app.acl_users)
    newSecurityManager(app, user)
    
    a_projects = get_active_projects()
    print len(a_projects)
