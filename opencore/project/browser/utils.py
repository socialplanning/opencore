import uuid

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
