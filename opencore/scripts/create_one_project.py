"""A quick hack to make lots of opencore projects.
hopefully useful for testing how things scale up.

Run this via zopectl run.
"""

from AccessControl.SecurityManagement import newSecurityManager
from Testing.makerequest import makerequest
from ZODB.POSException import ConflictError
import random
import sys
import time
import transaction

featurelets = ["listen"]
def main(app, proj_id, policy, proj_title, descr):
    user = app.acl_users.getUser('admin')
    print "Changing stuff as user", user
    newSecurityManager(None, user)
    app = makerequest(app)
    projfolder = app.openplans.projects


    projfolder.REQUEST.form.update({
        'featurelets': featurelets,
        'workflow_policy': policy,
        'description': descr,
        'set_flets': 1, # sacrifice a chicken to tell opencore not to ignore our featurelet creation request
        'featurelet_skip_content_init': 1, # but dont try to create featurelet content (e.g. project-discussion list)
        })

    projfolder.REQUEST.set('flet_recurse_flag', None) # sacrifice a goat too

    addview = projfolder.restrictedTraverse('@@create')

    projfolder.REQUEST.form.update({
            'project_title': proj_title,
            'projid': proj_id,
            })
    
    addview.handle_request()

    if addview.errors:
        for key, val in addview.errors.items():
            print "ERROR: %s: %s" % (key, val)
        raise RuntimeError("Project creation failed, see errors above.")
    print "created", proj_id


if __name__ == '__main__':
    main(app)