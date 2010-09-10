"""
Small helper methods supporting member-related OpenCore behaviour.
"""

from Products.CMFCore.utils import getToolByName
from opencore.member.interfaces import REMOVAL_QUEUE_KEY
from zope.annotation import IAnnotations
import logging

logger = logging.getLogger('opencore.member.utils')

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
    return '%s/profile' % member_path(mem_id)

def portrait_thumb_path(mem_id, thumbnail_name='thumb'):
    return '%s/portrait_%s' % (member_path(mem_id), thumbnail_name)


def get_cleanup_queue(context):
    """
    Find a queue that contains recently deleted member ids so we can
    clean up after them.
    """
    portal = getToolByName(context, 'portal_url').getPortalObject()
    queue = IAnnotations(portal)[REMOVAL_QUEUE_KEY]
    return queue

