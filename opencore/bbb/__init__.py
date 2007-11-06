from topp.utils.persistence import KeyedMap
import uuid


def bbb_keymap(wrap=True):
    """auto-migrater"""
    def wrap_func(func): 
        def wrap(*args, **kwargs):
            keymap = func(*args, **kwargs)
            if not isinstance(keymap, KeyedMap):
                address = args[1]
                key = hash(uuid.uuid4())
                return KeyedMap(btree=keymap, key=key)
            return keymap
        return wrap
    if wrap:
        return wrap_func
    else:
        return func
