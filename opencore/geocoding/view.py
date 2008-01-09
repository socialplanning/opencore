from Products.CMFCore.utils import getToolByName
from Products.PleiadesGeocoder.interfaces.simple import IGeoItemSimple
from opencore.i18n import _
from zope.app.publisher.interfaces.browser import IBrowserView
from zope.component import adapts
from zope.interface import implements
import Acquisition
import interfaces
import logging
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
        for key in ('position-text', 'location', 'position-latitude',
                    'position-longitude'):
            info[key] = context_info.get(key, '')
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
        coords = self._get_geo_item().coords
        if not coords:
            return ''
        lon, lat = coords[:2]
        return utils.location_img_url(lat, lon, width, height)


    
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

    def get_geo_info_from_form(self, form=None, old_info=None):
        """Returns a dict and a list: (info, changed), Just like
        utils.update_info_from_form, but you don't have to pass
        anything.

        No side effects, just returns stuff.
        XXX add to interface
        """
        if form is None:
            form = self.request.form
        if old_info is None:
            old_info = self.geo_info()
        new_info, changed = utils.update_info_from_form(
            self.geo_info(), form, self.view.get_tool('portal_geocoder'))
        self.view.errors.update(new_info.get('errors', {}))
        return new_info, changed


    def set_geo_info_from_form(self, form=None):
        """XXX add to interface."""
        new_info, changed = self.get_geo_info_from_form(form)
        lat = new_info.get('position-latitude')
        lon = new_info.get('position-longitude')
        if lat == '': lat = None
        if lon == '': lon = None
        self.set_geolocation((lat, lon))

    def geocode_from_form(self, form=None):
        """See IWriteGeo.
        """
        default = ()
        if not self.view.has_geocoder:
            return default
        if form is None:
            form = self.request.form
        position = form.get('position-text', '').strip()
        if position:
            # If we got this, then it overrides the other form variables.
            # The value should be something we can look up via the geocoder.
            geo_tool = self.context.get_tool('portal_geocoder')
            records = geo_tool.geocode(position)
            if records:
                lat = records[0]['lat']
                lon = records[0]['lon']
                return lat, lon
            else:
                self.view.errors['position-text'] = _(
                    u'psm_geocode_failed',
                    u"Sorry, we were unable to find that address on the map.")
                return default
        else:
            lon = form.get('position-longitude', '')
            lat = form.get('position-latitude', '')
            if lat == lon == '':
                # We got nothing in the form, that's OK.
                return default
            try:
                lat = float(lat)
                lon = float(lon)
            except (TypeError, ValueError):
                logger.error(
                    "bad map info from oc-js? got %s" % str(lat, lon))
                return default
            return (lat, lon)


class MemberareaReadGeoView(ReadGeoView):

    def _get_geo_item(self):
        return IGeoItemSimple(self.view.viewedmember())

class MemberareaWriteGeoView(WriteGeoView, ReadGeoView):
    pass


# We'd like to be able to get these wrapper views by just saying
# eg. IReadGeo(some_view), but that doesn't seem to work; The
# below works in zope 3.3, but not 2.9:
## from interfaces import IReadGeo
## provideAdapter(ReadGeoView, provides=IReadGeo)

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
    return wrapper.__of__(context)

# Ditto for WriteGeoView.
def getWriteGeoViewWrapper(view, context=None):
    context = context or view.context
    if IMemberFolder.providedBy(context):
        wrapper = MemberareaWriteGeoView(view, context)
    elif IContainer.providedBy(context):
        wrapper = WriteGeoView(view, context)
    else:
        raise TypeError("Couldn't adapt %r to IWriteGeoView." % view)
    return wrapper.__of__(context)

# TO DO: To allow opencore to work without this package, put default
# do-nothing IReadWriteGeo implementation in somewhere like
# browser/base and the implementations here can override that.
