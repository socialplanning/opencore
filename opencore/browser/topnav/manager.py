from Acquisition import aq_base
from opencore.browser.topnav.topnav_menuitem import BaseMenuItem
from opencore.interfaces import IOpenPage
from opencore.interfaces.adding import IAddProject
from opencore.interfaces.adding import IAmAPeopleFolder
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.interfaces import IPloneSiteRoot
from Products.Five.viewlet.manager import ViewletManagerBase
from Products.Five.viewlet.metaconfigure import viewletDirective
from topp.utils import zutils
from zope.interface import Interface

def contained_within(viewlet):
    return zutils.aq_iface(viewlet.context, viewlet.container)

def nofilter(viewlet):
    return True

def contained_item_url(viewlet):
    item = contained_within(viewlet)
    if item is None:
        url = viewlet.context.absolute_url()
    else:
        url = item.absolute_url()
    return '%s/%s' % (url, viewlet.item_url)

def portal_and_item_url(viewlet):
    portal = getToolByName(viewlet.context, 'portal_url').getPortalObject()
    return '%s/%s' % (portal.absolute_url(), viewlet.item_url)

def people_url(viewlet):
    portal = getToolByName(viewlet.context, 'portal_url').getPortalObject()
    return '%s/people' % portal.absolute_url()

def projects_url(viewlet):
    portal = getToolByName(viewlet.context, 'portal_url').getPortalObject()
    return '%s/projects' % portal.absolute_url()

def project_create_url(viewlet):
    portal = getToolByName(viewlet.context, 'portal_url').getPortalObject()
    return '%s/projects/create' % portal.absolute_url()

def member_wiki_url(viewlet):
    mstool = getToolByName(viewlet.context, 'portal_membership')
    home_folder = mstool.getHomeFolder()
    id_ = home_folder.getId()
    return '%s/%s-home' % (home_folder.absolute_url(), id_)

def project_wiki_url(viewlet):
    proj = contained_within(viewlet)
    return '%s/project-home' % proj.absolute_url()

def if_request_starts_with_url(viewlet):
    return viewlet.request.ACTUAL_URL.startswith(viewlet.url())

def if_portal_people_or_projects(viewlet):
    context = viewlet.context
    for iface in IPloneSiteRoot, IAddProject, IAmAPeopleFolder:
        if iface.providedBy(context):
            return True
    return False

def if_projects_selected(viewlet):
    return (IAddProject.providedBy(viewlet.context)
            and not viewlet.context.request.ACTUAL_URL.endswith('/create'))

def openpage_provided(viewlet):
    return IOpenPage.providedBy(viewlet.context)

def default_css(viewlet):
    return viewlet.selected() and 'oc-topnav-selected' or None

def join_css(viewlet):
    return viewlet.selected() and 'oc-topnav-selected' or 'oc-topnav-join'

def not_part_of_project(viewlet):
    proj = contained_within(viewlet)
    if proj is None:
        return False
    mstool = getToolByName(viewlet.context, 'portal_membership')
    if mstool.isAnonymousUser():
        return True
    mem = mstool.getAuthenticatedMember()
    team = proj.getTeams()[0]
    filter_states = tuple(team.getActiveStates()) + ('pending',)
    if mem.getId() in team.getMemberIdsByStates(filter_states):
        return False
    return True


class TopnavManager(ViewletManagerBase):
    """custom menu manager for opencore topnavigation"""

    def filter(self, viewlets):
        """also filter out viewlets by containment"""
        viewlets = super(TopnavManager, self).filter(viewlets)
        return [result for result in viewlets\
                if result[1].filter()]

    def sort(self, viewlets):
        """Sort the viewlets.

        ``viewlets`` is a list of tuples of the form (name, viewlet).
        """
        # By default, use the standard Python way of doing sorting. Unwrap the
        # objects first so that they are sorted as expected.  This is dumb
        # but it allows the tests to have deterministic results.
        return sorted(viewlets, lambda x, y: cmp(aq_base(x[1].sort_order), aq_base(y[1].sort_order)))

    @classmethod
    def create_topnav_viewlet(cls, name, sort_order,
                              text,
                              url,
                              item_url,
                              filter,
                              container,
                              css_class,
                              selected,
                              **kw
                              ):
        klass_name = "%s-%s" % (BaseMenuItem.__name__, str(name))
        attrs = dict(name=name,
                     text=text,
                     sort_order=sort_order,
                     url=url,
                     item_url=item_url,
                     filter=filter,
                     container=container,
                     css_class=css_class,
                     selected=selected,
                     )
        return type(klass_name, (BaseMenuItem,), attrs)                

            
def oc_menuitem_directive(_context, name, sort_order,
                          text=None,
                          permission='zope2.View',
                          url=contained_item_url,
                          item_url=u'',
                          filter=nofilter,
                          container=IPloneSiteRoot,
                          css_class=default_css,
                          selected=if_request_starts_with_url,
                          **kw):
    """create a class specific for viewlet"""
    new_keyword_args = kw.copy()
    if text is None:
        text = name
    viewlet_factory = TopnavManager.create_topnav_viewlet(
        name,
        sort_order,
        text,
        url,
        item_url,
        filter,
        container,
        css_class,
        selected,
        )
    new_keyword_args['class_'] = viewlet_factory
    new_keyword_args['manager'] = TopnavManager
    viewletDirective(_context, name, permission, **new_keyword_args)
