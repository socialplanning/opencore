from Products.PleiadesGeocoder.browser.info import GeoInfosetView

import cStringIO
import traceback
import logging

logger = logging.getLogger('opencore.geocoding.feeds')

_rss_head = '''<?xml version="1.0" encoding="utf-8"?>
<feed
 xmlns="http://www.w3.org/2005/Atom"
 xmlns:georss="http://www.georss.org/georss"
 xmlns:gml="http://www.opengis.net/gml">

<title>%(title)s</title>
<link rel="self" href="%(folder_url)s"/>
<updated/>
<author/>
<id>%(folder_url)s</id>

'''

_rss_point = '''<entry>
<title>%(title)s</title>
<link rel="alternate" href="%(link)s">%(link)s</link>
<id>%(link)s</id>
<updated>%(updated)s</updated>
<summary>%(description)s</summary>
<georss:where><gml:Point>
<gml:pos>%(coords_georss)s</gml:pos>
</gml:Point></georss:where>
</entry>
'''

_rss_linestring = '''<entry>
<title>%(title)s</title>
<link rel="alternate" href="%(link)s">%(link)s</link>
<id>%(link)s</id>
<updated>%(updated)s</updated>
<summary>%(description)s</summary>
<georss:where><gml:LineString>
<gml:posList>%(coords_georss)s</gml:posList>
</gml:LineString></georss:where>
</entry>
'''

_rss_polygon = '''<entry>
<title>%(title)s</title>
<link rel="alternate" href="%(link)s">%(link)s</link>
<id>%(link)s</id>
<updated>%(updated)s</updated>
<summary>%(description)s</summary>
<georss:where>
<gml:Polygon><gml:exterior><gml:LinearRing>
<gml:posList>%(coords_georss)s</gml:posList>
</gml:LinearRing></gml:exterior></gml:Polygon>
</georss:where>
</entry>
'''

_rss_tail = '\n</feed>\n'


class GeoRssView(GeoInfosetView):

    def georss(self):
        """Stream a GeoRSS xml feed for this container.
        """
        # XXX we should support conditional GET, if we had a way
        # to find out which items have changed coordinates.
        response = self.request.RESPONSE
        maxitems = int(self.request.form.get('maxitems', -1))
        response.setHeader('Content-Type',
                           'application/atom+xml; charset=utf-8')
        headinfo = {'folder_url': self.context.absolute_url(),
                    'title': self.context.title_or_id(),
                    }
        items = self.forRSS(maxitems)
        # Do streaming, old-school zserver & http 1.0 style.
        response._http_connection = 'close'
        response.http_chunk = 0
        response.setStatus(200)
        response.write(_rss_head % headinfo)
        try:
            for item in items:
                properties = item['properties']
                properties['description'] = properties.get('description') or 'None.'
                properties['coords_georss'] = item['coords_georss']
                if item['hasPoint']:
                    response.write(_rss_point % properties)
                elif item['hasLineString']:
                    response.write(_rss_linestring % properties)
                elif item['hasPolygon']:
                    response.write(_rss_polygon % properties)
                else:
                    pass
        except:
            # Yuck. ZServer can't tolerate exceptions once you've
            # started streaming with response.write().
            # Best we can do now is log the exception.
            f = cStringIO.StringIO()
            traceback.print_exc(file=f)
            logger.error(f.getvalue())
        response.write(_rss_tail)
        response.flush()
