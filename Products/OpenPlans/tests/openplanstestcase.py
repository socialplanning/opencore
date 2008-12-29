from BTrees.OOBTree import OOBTree
from Products.Archetypes.tests.atsitetestcase import ATSiteTestCase as ArcheSiteTestCase
from Products.CMFCore.utils  import getToolByName
from Testing.ZopeTestCase import PortalTestCase
from opencore.configuration.setuphandlers import migrateATDocToOpenPage
from opencore.testing.layer import OpenPlansLayer
from plone.memoize.instance import Memojito
from plone.memoize.view import ViewMemo
from zope.app.annotation.interfaces import IAnnotations
from zope.app.event.interfaces import IObjectEvent
from zope.component import provideHandler
from zope.interface import Interface

import opencore.utils

migrateOpenPage = migrateATDocToOpenPage.orig


# This is the test case. You will have to add test_<methods> to your
# class in order to assert things about your Product.
class OpenPlansTestCase(ArcheSiteTestCase):

    layer = OpenPlansLayer

    def afterSetUp(self):
        ArcheSiteTestCase.afterSetUp(self)
        self.loginAsPortalOwner()
        
        # Because we add skins this needs to be called. Um... ick.
        self._refreshSkinData()
        self.login()
        mdc = getToolByName(self.portal, 'portal_memberdata')
        mdc.unit_test_mode = True # suppress registration emails

        # add event subscriber to listen to all channel events
        self.listen_for_object_events()

    @classmethod
    def patch_wordpress_handlers(cls):
        """All wordpress handlers involve sending a message to wordpress
           on a different port. We patch the sending, so the methods still get
           triggered, they just don't get sent anywhere"""
        def patched_send_to_wordpress(uri, username, params, context):
            pass

        import opencore.wordpress.events
        opencore.wordpress.events.send_to_wordpress = patched_send_to_wordpress

    def listen_for_object_events(self):
        """listen for all events so that tests can verify they were sent

           events are stored in the test case "events" attribute"""

        self.events = events = []
        def generic_listener(obj, event):
            events.append((obj, event))
        provideHandler(generic_listener, adapts=[Interface, IObjectEvent])

    def clear_events(self):
        self.events[:] = []

    def event_fired(self, iface):
        """
        returns True if one or more of the fired events provides
        the specified interface
        """
        for mship, event in self.events:
            if iface.providedBy(event):
                return True

    def tearDown(self):
        # avoid any premature tearing down
        PortalTestCase.tearDown(self)

    def clearMemoCache(self):
        # from the request
        req = self.portal.REQUEST
        annotations = IAnnotations(req)
        cache = annotations.get(ViewMemo.key, None)
        if cache is not None:
            annotations[ViewMemo.key] = dict()
        # from the timestamp cache
        opencore.utils.timestamp_cache.clear()

    def clearInstanceCache(self, obj):
        propname = Memojito.propname
        try:
            delattr(obj, propname)
        except AttributeError:
            pass

    def createClosedProject(self, proj_id):
        proj_folder = self.portal.projects
        from opencore.interfaces.adding import IAddProject
        IAddProject.providedBy(proj_folder)

        proj = proj_folder.restrictedTraverse(
          'portal_factory/OpenProject/%s' % proj_id)
        proj_folder.portal_factory.doCreate(proj, proj_id)
        closed_proj = proj_folder._getOb(proj_id)

        # now make it closed
        wft = getToolByName(self.portal, 'portal_workflow')
        wfid = 'openplans_teamspace_workflow'
        status = wft.getStatusOf(wfid, closed_proj)
        status['review_state'] = 'closed'
        wft.setStatusOf(wfid, closed_proj, status)

        # and reindex for good measure
        closed_proj.reindexObject()

        return closed_proj
