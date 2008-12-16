from Products.CMFCore.utils import getToolByName
from opencore.project.utils import project_noun
from topp.utils.pretty_date import prettyDate
from zope import component
from zope import interface
from zope.app.component.hooks import getSite
from zope.traversing.interfaces import IPathAdapter

class OpencoreTales(object):
    component.adapts(interface.Interface)
    interface.implements(IPathAdapter)

    def __init__(self, context):
        if callable(context):
            # XXX Are we sure we want to do implicitly call here?
            # This can easily lead to infinite recursion, eg. if our
            # TALES expression is used in the default view on a
            # context, because calling the object invokes the default
            # view again.
            self.context = context()
        else:
            self.context = context

    def pretty_date(self):
        return prettyDate(self.context)

    def project_noun(self):
        return project_noun()

    def member_title(self):
        if isinstance(self.context, basestring):
            return member_title(self.context)
        elif isinstance(self.context, dict):
            # No need to do all those lookups.
            return self.context['fullname'].strip() or self.context['id']
        else:
            raise TypeError('member_title expected a string id or '
                            'memberdata dict as context, got %s'
                            % str(self.context))


def member_title(id):
    # Backported from sputnik.utils.
    context = getSite()
    pid = getToolByName(context, 'portal_url').getPortalObject().id
    mt = getToolByName(context, 'membrane_tool')
    try:
        meta = mt.getMetadataForUID('/%s/portal_memberdata/%s' % (pid, id))
        return meta['Title']
    except KeyError:
        #if not in the catalog, fall back on the member id
        return id
