# run via zopectl run

"""A quick hack to make lots of opencore projects.
hopefully useful for testing how things scale up.
"""
from AccessControl.SecurityManagement import newSecurityManager
from Testing.makerequest import makerequest
from ZODB.POSException import ConflictError
import random
import sys
import time
import transaction

def add(container, pid, lat, lon):
    pass

descr = """Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Etiam
pretium rhoncus neque. Suspendisse nec lectus non purus mattis
vestibulum. Suspendisse vitae leo quis nulla convallis
imperdiet.
"""

def main(app, count=1):
    user = app.acl_users.getUser('admin')
    print "Changing stuff as user", user
    newSecurityManager(None, user)
    app = makerequest(app)
    projfolder = app.openplans.projects
    projfolder.REQUEST.form.update({
        'featurelets': [],  # don't use wordpress, et al.
        'workflow_policy': 'open_policy',
        'description': descr,
        })
    batchsize = 10
    i = 0
    while i < count:
        addview = projfolder.restrictedTraverse('@@create')
        proj_id = 'project_%04d_%d' % (i, int(time.time()))
        # might as well try to keep it in the continental US.
        lat = random.uniform(30.0, 50.0)
        lon = random.uniform(80.0, 120.0)
        projfolder.REQUEST.form.update({
            'project_title': proj_id,
            'projid': proj_id,
            'position-latitude': lat,
            'position-longitude': lon,
            'location': 'somewhere %d' % i,
            })
        addview.handle_request()
        if addview.errors:
            for key, val in addview.errors.items():
                print "ERROR: %s: %s" % (key, val)
            raise RuntimeError("Project creation failed, see errors above.")
        print "created", proj_id
        conflicts = 0
        if i and i % batchsize == 0:
            try:
                transaction.commit()
                conflicts = 0
            except ConflictError:
                # I don't really know why these happen on a totally
                # unloaded site.
                conflicts += 1
                if conflicts > 3:
                    raise
                print "Conflict error, retrying the last %d" % batchsize
                transaction.abort()
                app._p_jar.sync()
                i -= batchsize
        i += 1
    transaction.commit()


main(app, count=int(sys.argv[1]))
