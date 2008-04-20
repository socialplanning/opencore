from opencore.member.transient_messages import *
from persistent import Persistent

class TransientMessage(TransientMessage, Persistent):
    """to allow the cache to be happy"""
