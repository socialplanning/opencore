Create a stub object
    >>> class Dummy(object):
    ...     pass
    >>> dummy = Dummy()

Mark it as annotatable
    >>> alsoProvides(dummy, IAttributeAnnotatable)
    >>> IAttributeAnnotatable.providedBy(dummy)
    True

And declare the adapter for IAnnotations
This is only necessary in a test, otherwise this would normally be declared
    >>> provideAdapter(AttributeAnnotations)

And now let's declare an adapter for IGeoLocation
    >>> from opencore.geolocation.interfaces import IGeoLocation
    >>> from opencore.geolocation.location import GeoLocation
    >>> provideAdapter(GeoLocation)

Now we can adapt the dummy object to IGeoLocation
    >>> gl = IGeoLocation(dummy)

When we try to get something out of it without storing something first,
a ValueError should get raised
    >>> gl.latitude_longitude()
    Traceback (most recent call last):
    ...
    ValueError: No latitude, longitude

Store a lat/lon pair
    >>> gl.store_latitude_longitude((3, 4))

Now we can retrieve the pair
    >>> gl.latitude_longitude()
    (3, 4)
