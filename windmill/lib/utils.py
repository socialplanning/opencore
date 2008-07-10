from fassembler.configparser.configparser import get_config
from functest import registry
from xmlrpclib import Server

import logging
import urllib

logger = logging.getLogger('opencore.windmill')

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
        
