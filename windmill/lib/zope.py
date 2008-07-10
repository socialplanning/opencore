from utils import get_auth_portal
from xmlrpclib import Fault

def zope_delobject(container_path, obj_id):
    """
    Deletes a Zope object:

    o container_path: path to the container of the object to be
    deleted, relative to the Plone site root

    o obj_id: id of the object to be deleted
    """
    portal = get_auth_portal()
    try:
        getattr(portal, container_path).manage_delObjects([obj_id])
    except Fault, e:
        ignorable = '%s does not exist' % obj_id
        if str(e).count(ignorable):
            print("(zope) can't delete %s/%s, it didn't exist" % (container_path,
                                                                  obj_id))
        else:
            print("Error removing '%s' from '%s': %s" % (obj_id,
                                                         container_path,
                                                         str(e)))
