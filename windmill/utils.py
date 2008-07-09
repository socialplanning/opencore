from fassembler.configparser.configparser import get_config
from functest import registry
from xmlrpclib import Server
from xmlrpclib import Fault

import urllib

base_url = registry['url']

def get_admin_info():
    """
    Returns tuple of admin userid, admin password.
    """
    f = open(get_config('admin_info_filename'))
    info = f.read().strip()
    uid, pwd = info.split(':')
    return (uid, pwd)
    
def get_auth_portal():
    """
    Returns an XML-RPC server object that maps to the Plone site root,
    authenticated as an admin user.
    """
    admin_uid, admin_pwd = get_admin_info()
    scheme, uri = urllib.splittype(base_url) 
    host, path = urllib.splithost(uri)
    auth_url = "%s://%s:%s@%s%s/" % (scheme, admin_uid, admin_pwd, host, path)
    return Server(auth_url)

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
        
