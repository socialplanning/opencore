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

proj_id = sys.argv[-4]
policy = sys.argv[-3]
proj_title = sys.argv[-2]
descr = sys.argv[-1]
featurelets = ["listen"] #@@TODO

def main(app):
    user = app.acl_users.getUser('admin')
    print "Changing stuff as user", user
    newSecurityManager(None, user)
    app = makerequest(app)
    projfolder = app.openplans.projects
    projfolder.REQUEST.form.update({
        'featurelets': featurelets,
        'workflow_policy': policy,
        'description': descr,
        })

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

    transaction.commit()


main(app)
