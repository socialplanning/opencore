import uuid
from topp.utils.persistence import KeyedMap

class vdict(dict):
    _sortable = dict(id=None,
                     url=None,
                     obj_size=None,
                     obj_date=None,
                     obj_author=None,
                     title='sortable_title')

    def __init__(self, header, _editable, **extra):
        self.header = header
        self.editable = _editable
        self['id'] = 'getId'
        self['title'] = 'Title'
        self['url'] = 'getURL'
        self.update(extra)
        
    def sortable(self, prop):
        """
        Returns the string to pass in to a catalog query sort_on
        for a given property; if there is no way to sort on that
        property, returns False
        """
        if prop not in self._sortable.keys():
            return False
        key = self._sortable[prop] or self.get(prop)
        if not key:
            return False
        return key

def make_key():
    return uuid.uuid4().bytes.encode('base64')[:-3]

def bbb_keymap(wrap=True):
    """auto-migrater"""
    def wrap_func(func): 
        def wrap(*args, **kwargs):
            keymap = func(*args, **kwargs)
            if not isinstance(keymap, KeyedMap):
                address = args[1]
                key = utils.make_key()
                return KeyedMap(btree=keymap, key=key)
            return keymap
        return wrap
    if wrap:
        return wrap_func
    else:
        return func


def google_e6_encode(lat_or_lon):
    """Google makes life easy for themselves, and harder for us, by
    encoding signed float latitude and longitude into unsigned integers.

    >>> google_e6_encode(1)
    1000000
    >>> google_e6_encode(1.0)
    1000000
    >>> google_e6_encode(0)
    0
    >>> # Negatives get offset by 2 ** 32.
    >>> google_e6_encode(-1)
    4293967296
    >>> 2 ** 32 - google_e6_encode(-1)
    1000000
    >>> google_e6_encode(40.737562)
    40737562
    >>> google_e6_encode(-74.00709)
    4220960206
    """
    lat_or_lon *= 1000000
    if lat_or_lon < 0:
        lat_or_lon = 2 ** 32 + lat_or_lon
    return int(lat_or_lon)
