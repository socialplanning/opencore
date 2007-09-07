import logging
import urllib2
from lxml import etree

from Products.CMFCore.utils import getToolByName

histfile = None
LOG = logging.getLogger("OpenPlans")

def output(obj, nversions=0):
    """ output a line for the history checker """

    global histfile

    if not histfile:
        histfile = file('histfile.txt', 'w', 0)
        
    url = obj.absolute_url()
    title = obj.title
    line = ','.join((url, title, str(nversions)))
    if line.encode:
        line = line.encode('ascii', 'xmlcharrefreplace')
    print >> histfile, line

def checkhistory(self):
    """ 
    check the history of the whole plone site.
    useful for comparing data pre- to post- migrating CMFEditions 
    """

    catalog = getToolByName(self, 'portal_catalog')

    nitems = nversionable_items = nitems_with_history = 0
    nghosts = 0
    brains = catalog(portal_type='Document', sort_on='UID')
    ntot = len(brains)
    for brain in brains:        
        nitems += 1
        LOG.info('Processing item ' + str(nitems) + ' of ' + str(ntot) + ' ...')

        try:
            i = brain.getObject()
        except AttributeError:
            LOG.warn('Encountered catalog ghost, removing...')
            catalog._catalog.uncatalogObject(brain.getPath()) # catalog uses path as internal uid
            nghosts += 1
            LOG.warn('Ghost removal done')
            continue

        LOG.info('- class:' + repr(i.__class__))
        LOG.info('- title:' + i.title.__repr__())
        LOG.info('- url:' + i.absolute_url())

        try:
            html = i.versions_history_form()

            tree = etree.HTML(html)
            table = tree.xpath("//*[@id='sortable']")
            nversionable_items += 1            

            if table:
                nitems_with_history += 1
                nversions = len(table[0][1])
                output(i, nversions)
            else:
                output(i)

        except urllib2.HTTPError:
            pass

        LOG.info('Item ' + str(nitems) + ' done')
        

    LOG.info('---- SCRIPT FINISHED ----')
    endstring = '%s items checked, %s versionable items, %s items with history, %s ghosts removed' % ( nitems,
                                                                                                       nversionable_items,
                                                                                                       nitems_with_history,
                                                                                                       nghosts )
    LOG.info(endstring)
    return endstring
