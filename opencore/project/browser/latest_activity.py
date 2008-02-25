import re

from opencore.project.browser.latest_snippet import LatestSnippet
from opencore.project.browser.contents import ProjectContentsView
from opencore.project.utils import get_featurelets
from Products.CMFCore.utils import getToolByName
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from Products.listen.interfaces import ISearchableArchive
from Products.listen.lib.browser_utils import messageStructure
from zope.component import getUtility

class ListFromCatalog(object):
    """
    return the latest items from a catalog
    """

    keys = [ 'portal_type', 'path' ]

    def __init__(self, portal_type, path):
        self.base_query = dict([(key, locals()[key]) for key in self.keys])

    def query(self):        
        return dict(sort_order='descending',
                    sort_on='Date', **self.base_query)

    def __call__(self, catalog, number=None):
        items = catalog(**self.query())
        if number is None:
            number = len(items)
        return items[:number]

class DiscussionList(ListFromCatalog):
    """rediculously bad class to get mail"""

    def __call__(self, catalog, number=None):
        lists = catalog(**self.base_query)
        items = []
        for mlist in lists:
            mlist = mlist.getObject()
            archive = getUtility(ISearchableArchive, context=mlist)
            messages = archive.getToplevelMessages()
            messages = [ dict(message=message,
                              structure=messageStructure(message, sub_mgr=mlist))
                         for message in messages ]
            if len(lists) > 1:
                for message in messages:
                    message['structure']['list'] = mlist.title
                    message['structure']['list_url'] = mlist.absolute_url()
            items.extend(messages)
        date_cmp = lambda x, y: cmp(x['message'].modification_date,
                                    y['message'].modification_date) 
        items.sort(date_cmp, reverse=True) # reverse date compare
        if number is None:
            number = len(items)
        return items[:number]

class Feed(object):
    """a rediculously stupid class for feeds.
    should be redone"""
    def __init__(self, title, link, linktitle, listgetter, listgetterargs,
                 tofeed, tofeedargs=None):
        self.title = title
        self.link = link
        self.linktitle = linktitle
        self.listgetter = listgetter
        if listgetterargs is None:
            listgetterargs = ( [], {} )
        self.listgetterargs = listgetterargs 
        self.tofeed = tofeed
        if tofeedargs is None:
            tofeedargs = ( [],{} )
        self.tofeedargs = tofeedargs

    def getlist(self):
        return self.listgetter(*self.listgetterargs[0], **self.listgetterargs[1])

    def getfeeds(self):
        return [ self.tofeed(source, self.tofeedargs) for source in self.getlist() ]



def project2feed(project_brains, args):
    member_url = args[0][0] # this is a hack for a quick checkin :(
    author = project_brains.lastModifiedAuthor    
    if author:
        author_url = member_url(author).rstrip('/') + '/profile'
        author = { 'home': author_url, 'userid': author }
    else:
        author = { 'home': '', 'userid': '' }
    return { 'title': project_brains.Title,
             'url': project_brains.getURL(),
             'author': author,
             'date': project_brains.ModificationDate,
             }

def discussions2feed(message, args):
    member_url = args[0][0]
#    author = message.getOwner().getUserName()
    author = message['structure']['from_id']
    if author:
        author_url = member_url(author).rstrip('/') + '/profile'
        author = { 'home': author_url, 'userid': author }
    else:
        userid = message['structure']['mail_from'] 
        match = re.match(r' *"(.*)" *<.*@.*>', userid)
        if match:
            userid = match.groups()[0]
        author = { 'home': '', 'userid': userid }

    responses = message['message'].responses
    
    retval = { 'title': message['message'].subject,
               'url': message['structure']['url'],
               'author': author,
               'date': message['message'].modification_date,
               'responses': { 'number': responses,
                              'url': message['structure']['url'], }
               }

    if message['structure'].has_key('list'):
        retval['context'] = { 'title': message['structure']['list'],
                              'url': message['structure']['list_url'], }

    return retval

class LatestActivityView(ProjectContentsView):
    """
    displays latest activity for a project.
    This is a concept class (sandbox) for the time being
    I think/hope the appropriate architecture will
    emerge from playing with it
    """

    # XXX this is necessary because the ProjectContentsView stupidly overrides template
    template = ZopeTwoPageTemplateFile('latest_activity.pt')    

    def __init__(self, context, request):                
        ProjectContentsView.__init__(self, context, request)
#        globals()['mtool'] = getToolByName(self.context, 'portal_membership')
        self.feed_types = []
        self.feed_types.append(Feed('Pages',
                                    '/'.join((self.area.absolute_url(),
                                              'project-home')),
                                    'MORE PAGES',
                                    ListFromCatalog(self._portal_type['pages'], self.project_path),
                                    ([self.catalog], dict(number=5)),
                                    project2feed, ( [ self.memfolder_url ], {}), ),
                               )

        if self.has_mailing_lists:
            self.feed_types.append(Feed('Discussions',
                                        '/'.join((self.area.absolute_url(),
                                                  self._get_featurelet('listen')['url'])),
                                        'MORE THREADS',
                                        DiscussionList(self._portal_type['lists'], self.project_path),
                                        ([self.catalog], dict(number=5)),
                                         discussions2feed, ( [ self.memfolder_url ], {}),),
                                   )

        # XXX this logic should live at a higher level
        # maybe project base view
        self.logo_url = context.getLogo()
        if self.logo_url:
            self.logo_url = self.logo_url.absolute_url()
        else:
            self.logo_url = self.defaultProjLogoThumbURL
        
    def snippet(self, feed):
        snip = self.context.unrestrictedTraverse('latest-snippet')
        snip.feedtitle = feed.title
        snip.link = feed.link
        snip.linktitle = feed.linktitle
        snip.items = feed.getfeeds()
        return snip()

    def feeds(self):
        feeds = []
        if self.has_blog:

            # add parameters to the request
            self.request['uri'] = '/'.join((self.context.absolute_url(),
                                            self._get_featurelet('blog')['url']))
            self.request['title'] = 'Blog'
            self.request['subtitle'] = 'MORE POSTS'
            

            # render the view
            blogfeed = self.context.restrictedTraverse('wordpressfeed')
            feeds.append(blogfeed())

        # extend (legacy) feeds
        feeds.extend( [ self.snippet(feed) for feed in self.feed_types ] )
        return feeds        

    def activity(self):
        f = ListFromCatalog(portal_type='Document', path=self.project_path)
        g = self.context.unrestrictedTraverse('latest-snippet')
        foo = g()

    def team_manager(self):
        """returns whether the member has permission to manage the team"""
        mem_id = self.member_info.get('id')
        if mem_id is None:
            return False
        return self.get_tool('portal_teams')._getOb(self.area.id).getHighestTeamRoleForMember(mem_id) == 'ProjectAdmin'

    def team_members(self):
        # XXX don't know if this is replicated elsewhere
        team = self.area.getTeams()
        assert len(team) == 1
        team = team[0]
        team = [ self.member_info_for_member(member)
                 for member in team.getActiveMembers() ]
        def team_sort(x, y):
            """sorting function for member display on project latest activity page"""
            # could also sort by admin-ness, lastlogin, etc
            portrait = [ x['portrait_url'], y['portrait_url'] ]
            default = '++resource++img/default-portrait.gif'
            portrait = [ int(i != default) for i in portrait ]
            return cmp(*portrait)

        team.sort(team_sort, reverse=True)
        return team
