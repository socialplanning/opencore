"""
Small helper methods supporting member-related OpenCore behaviour.
"""

def member_path(mem_id):
    """
    Returns the specified member's home folder path relative to the
    site root.
    """
    return "people/%s" % mem_id

def profile_path(mem_id):
    """
    Returns the specified member's profile page relative to
    the site root.
    """
    return '%s/profile' % mem_id
