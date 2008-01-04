from Products.CMFCore.utils import getToolByName
from Products.PleiadesGeocoder.interfaces.simple import IGeoItemSimple
from opencore.i18n import _
from zope.app.publisher.interfaces.browser import IBrowserView
from zope.component import adapts
from zope.component import provideAdapter
from zope.interface import implements
import Acquisition
import interfaces
import logging
import urllib
import utils

logger = logging.getLogger('opencore.geocoding')

class ReadGeoView(Acquisition.Explicit):

    """wraps an opencore view with geo functionality."""

    implements(interfaces.IReadGeo)
    adapts(IBrowserView)

    def __init__(self, view, context=None):
        # Need optional context arg for when wrapping an add view
        # and the context we care about is the thing to be added.
        # XXX Cleaner way to do that?
        self.view = view
        self.context = context or view.context
        self.request = view.request

    def geo_info(self):
        """See IReadGeo"""
        info = {'static_img_url': self.location_img_url(),
                'is_geocoded': self.is_geocoded(),
                'maps_script_url': self._maps_script_url()}
        if self.view.inmember:
            context_info = self.view.viewed_member_info
        else:
            # assume project.
            context_info = self.view.project_info
        _marker = object()
        for key in ('position-text', 'location', 'position-latitude',
                    'position-longitude'):
            if self.view.request.form.get(key, _marker) is not _marker:
                info[key] = self.view.request.form[key]
            elif context_info.get(key, _marker) is not _marker:
                info[key] = context_info[key]
            else:
                info[key] = ''
        return info

    def _get_geo_item(self):
        return IGeoItemSimple(self.context)

    def _maps_script_url(self):
        if not self.view.has_geocoder:
            return ''
        key = self.view.get_opencore_property('google_maps_key')
        if not key:
            logger.warn("you need to set a google maps key in opencore_properties")
            return ''
        url = "http://maps.google.com/maps?file=api&v=2&key=%s" % key
        return url

    def has_geocoder(self):
        """See IReadGeo. Is a PleiadesGeocoder tool available?
        """
        return getToolByName(self.context, 'portal_geocoder', None) is not None

    def is_geocoded(self):
        """See IReadGeo."""
        coords = self._get_geo_item().coords
        return bool(coords and not None in coords)

    def get_geolocation(self):
        """See IReadGeo. Note the output is ordered as (lon, lat, z)."""
        return self._get_geo_item().coords

    def location_img_url(self, width=500, height=300):
        """See IReadGeo."""
        geo = self._get_geo_item()
        if not geo.coords:
            return ''
        lon, lat, z = geo.coords
        # Don't know if order matters to Google; assume it does.
        params = (('latitude_e6', utils.google_e6_encode(lat)),
                  ('longitude_e6', utils.google_e6_encode(lon)),
                  ('w', width), ('h', height), # XXX These must match our css.
                  ('zm', 9600),  # Initial zoom.
                  ('cc', ''), # No idea what this is.
                  )
        url = 'http://maps.google.com/mapdata?' + urllib.urlencode(params)
        return url


class WriteGeoView(ReadGeoView):

    implements(interfaces.IWriteGeo)

    def set_geolocation(self, coords):
        """See IWriteGeo."""
        if coords and not None in coords:
            geo = self._get_geo_item()
            # XXX need to handle things other than a point!
            lat, lon = coords[:2]
            # Longitude first! Yes, really.
            new_coords = (lon, lat, 0.0)
            if new_coords != geo.coords:
                geo.setGeoInterface('Point', new_coords)
                return True
        return False

    def geocode_from_form(self, form=None):
        """See IWriteGeo.

        If no values are provided, return an empty sequence.

        If position is provided but can't be geocoded, raise ValueError.

        If latitude or longitude values are provided but no good, raise the
        underlying ValueError or TypeError.
        """
        default = ()
        if not self.view.has_geocoder:
            return default
        if form is None:
            form = self.request.form
        def error():
            self.view.errors['position-text'] = _(u'psm_geocode_failed', u"Sorry, we were unable to find that address on the map")
            return default
        position = form.get('position-text', '').strip()
        if position:
            # If we got this, then presumably javascript was disabled;
            # it overrides the other form variables.
            # The value should be something we can look up via the geocoder.
            geo_tool = self.context.get_tool('portal_geocoder')
            records = geo_tool.geocode(position)
            if records:
                lat = records[0]['lat']
                lon = records[0]['lon']
                return lat, lon
            else:
                return error()
        else:
            lon = form.get('position-longitude')
            lat = form.get('position-latitude')
            if lat is None or lon is None:
                return ()
            try:
                lon = float(lon)
                lat = float(lat)
            except TypeError:
                return error()
            return (lat, lon)


class MemberareaReadGeoView(ReadGeoView):

    def _get_geo_item(self):
        return IGeoItemSimple(self.view.viewedmember())

class MemberareaWriteGeoView(WriteGeoView, ReadGeoView):
    pass


# We'd like to be able to get these wrapper views by just saying
# eg. IReadGeoView(some_view), but that doesn't seem to work; The
# below is sufficient to make it work in zope 3.3, but not 2.9:
from interfaces import IReadGeo, IWriteGeo, IReadWriteGeo
provideAdapter(ReadGeoView, provides=IReadGeo)
provideAdapter(WriteGeoView, provides=(IWriteGeo, IReadWriteGeo))
provideAdapter(MemberareaReadGeoView, provides=IReadGeo)
provideAdapter(MemberareaWriteGeoView, provides=(IWriteGeo, IReadWriteGeo))

# So instead for now we'll use factory functions and not the
# component architecture.
from zope.app.container.interfaces import IContainer
from opencore.interfaces import IMemberFolder
def getReadGeoViewWrapper(view, context=None):
    context = context or view.context
    if IMemberFolder.providedBy(view.context):
        wrapper = MemberareaReadGeoView(view, context)
    elif IContainer.providedBy(view.context):
        wrapper = ReadGeoView(view, context)
    else:
        raise TypeError("Couldn't adapt %r to IReadGeoView." % view)
    return wrapper.__of__(view.context)

# Ditto for WriteGeoView.
def getWriteGeoViewWrapper(view, context=None):
    context = context or view.context
    if IMemberFolder.providedBy(context):
        wrapper = MemberareaWriteGeoView(view, context)
    elif IContainer.providedBy(context):
        wrapper = WriteGeoView(view, context)
    else:
        raise TypeError("Couldn't adapt %r to IWriteGeoView." % view)
    return wrapper.__of__(view.context)

# TO DO: To allow opencore to work without this package, put default
# do-nothing IReadWriteGeo implementation in somewhere like
# browser/base and the implementations here can override that.
