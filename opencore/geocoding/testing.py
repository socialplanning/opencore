from Products.Five.site.localsite import enableLocalSiteHook
from Products.PleiadesGeocoder.geocode import Geocoder
from opencore.testing import setup as oc_setup
from opencore.testing.minimock import Mock
from zope.app.component.hooks import setSite, setHooks

mock_geocode = Mock(
        'Products.PleiadesGeocoder.geocode.Geocoder.geocode')
mock_geocode.mock_returns = [{'place':  'mock place',
                              'lat': 12.0, 'lon': -87.0}]

_marker = object()
class MockGeocoder:

    """Useful for simpler tests that don't need a full zope context.
    Optionally initialize with stuff you want it to return. """

    def __init__(self, returnval=_marker):
        self.returnval = returnval

    def geocode(self, *args, **kw):
        result = mock_geocode()
        if self.returnval is _marker:
            return result
        else:
            return self.returnval

def setup_mock_geocoder():
    # useful for stuff that expects to use a PleiadesGeocoder tool instance.
    # XXX maybe move this to a layer.
    if hasattr(Geocoder, '_orig_geocode'):
        return
    Geocoder._orig_geocode = Geocoder.geocode
    Geocoder.geocode = mock_geocode

def restore_geocoder():
    if hasattr(Geocoder, '_orig_geocode'):
        Geocoder.geocode = Geocoder._orig_geocode
        del(Geocoder._orig_geocode)


def readme_setup(tc):
    oc_setup.fresh_skin(tc)
    enableLocalSiteHook(tc.portal)
    setSite(tc.portal)
    setHooks()
    setup_mock_geocoder()

def readme_teardown(tc):
    restore_geocoder()
