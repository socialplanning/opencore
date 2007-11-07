from topp.utils.persistence import KeyedMap
from opencore.nui.project.email_invites import EmailInvites 
import uuid


def bbb_keymap(wrap=True):
    """auto-migrater"""
    def wrap_func(func): 
        def wrap(*args, **kwargs):
            keymap = func(*args, **kwargs)
            if not isinstance(keymap, KeyedMap):
                address = args[1]
                key = EmailInvites.make_key()
                return KeyedMap(btree=keymap, key=key)
            return keymap
        return wrap
    if wrap:
        return wrap_func
    else:
        return func
