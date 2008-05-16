from zope.schema.fieldproperty import FieldProperty

from utils import getSuffix

class ListNameFieldProperty(FieldProperty):
    """
    Appends the right list hostname to the end of the list name
    prefix.
    """
    def __set__(self, inst, value):
        # something weird happening w/ name mangling here, self.__field
        # doesn't work
        field = self._FieldProperty__field.bind(inst)
        field.validate(value)
        name = self._FieldProperty__name
        if field.readonly and inst.__dict__.has_key(name):
            raise ValueError(name, 'field is readonly')
        suffix = getSuffix()
        inst.__dict__[name] = value.strip() + suffix
