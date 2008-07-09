from fassembler.configparser.configparser import get_config

def get_admin_info():
    """
    Returns tuple of admin userid, admin password.
    """
    f = open(get_config('admin_info_filename'))
    info = f.read().strip()
    uid, pwd = info.split(':')
    return (uid, pwd)
    
