from Products.CMFCore.utils import getToolByName
from Products.PleiadesGeocoder.interfaces.simple import IGeoItemSimple
from opencore.configuration.utils import get_config
from opencore.interfaces import IProject
from opencore.member.interfaces import IOpenMember
from urlparse import urlparse
from zope.app.publisher.interfaces.browser import IBrowserView
from zope.component import adapts
from zope.interface import implements
import Acquisition
import interfaces
import logging
import utils
import warnings

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

    def _get_viewedcontent(self):
        # I tried to call self.view.piv.project and .inproject, et al. but
        # for some reason those return None and False on a closed project.
        # Instead, we walk the acquisition chain by hand. Yuck.
        chain = self.context.aq_inner.aq_chain
        for item in chain:
            if IProject.providedBy(item):
                return item
            elif IOpenMember.providedBy(item):
                return item
        # If we get here, it typically means we're in eg. the projects
        # folder because our view is an add view and the project doesn't
        # exist yet. That's OK, we just won't have as much information.
        return None

    def geo_info(self):
        """See IReadGeo"""
        info = {'static_img_url': self.location_img_url(),
                'is_geocoded': self.is_geocoded(),
                'maps_script_url': self._maps_script_url()}
        content = self._get_viewedcontent()
        info['location'] = content and content.getLocation() or ''
        info['position-text'] = content and content.getPositionText() or ''
        coords = self.get_geolocation()
        try:
            lon, lat = coords[:2]
        except (ValueError, TypeError):
            lon, lat = '', ''
        info['position-latitude'] = lat
        info['position-longitude'] = lon
        return info

    def _get_geo_item(self):
        return IGeoItemSimple(self.context)

    def _maps_script_url(self):
        if not self.view.has_geocoder:
            return ''
        url = self.request['ACTUAL_URL']
        # In python 2.5, this could be written as urlparse(url).hostname
        hostname = urlparse(url)[1].split(':')[0]
        # We have a map key for each possible hostname in build.ini.
        key = get_config('google_maps_keys', hostname)
        if not key:
            warnings.warn("need a google maps key for %r" % hostname)
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
        """See IWriteGeo.
        """
        if form is None:
            form = self.request.form
        if old_info is None:
            old_info = self.geo_info()
        new_info, changed = utils.update_info_from_form(
            self.geo_info(), form, self.view.get_tool('portal_geocoder'))
        self.view.errors.update(new_info.get('errors', {}))
        return new_info, changed


    def save_coords_from_form(self, form=None):
        """See IWriteGeo."""
        new_info, changed = self.get_geo_info_from_form(form)
        lat = new_info.get('position-latitude')
        lon = new_info.get('position-longitude')
        if lat == '': lat = None
        if lon == '': lon = None
        self.set_geolocation((lat, lon))
        return new_info, changed



class MemberareaReadGeoView(ReadGeoView):

    def _get_geo_item(self):
        return IGeoItemSimple(self.view.viewedmember())

    def _get_viewedcontent(self):
        return self.view.viewedmember()

class MemberareaWriteGeoView(MemberareaReadGeoView, WriteGeoView):
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
def get_geo_reader(view, context=None):
    context = context or view.context
    if IMemberFolder.providedBy(view.context):
        wrapper = MemberareaReadGeoView(view, context)
    elif IContainer.providedBy(view.context):
        wrapper = ReadGeoView(view, context)
    else:
        raise TypeError("Couldn't adapt %r to IReadGeoView." % view)
    return wrapper.__of__(context)

# Ditto for WriteGeoView.
def get_geo_writer(view, context=None):
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
