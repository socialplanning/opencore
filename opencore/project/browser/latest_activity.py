from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile

from opencore.project.utils import get_featurelets

from opencore.project.browser.latest_snippet import LatestSnippet
from opencore.project.browser.view import ProjectContentsView


class ListFromCatalog:
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
            for year in mlist.getObject().archive.values():
                for month in year.values():
                    items.extend(month.values())
        date_cmp = lambda x, y: cmp(x.date, y.date)
        items.sort(date_cmp)
        if number is None:
            number = len(items)
        return items

class Feed:
    """a rediculously stupid class for feeds.
    should be redone"""
    def __init__(self, title, listgetter, listgetterargs,
                 tofeed, tofeedargs=None):
        self.title = title
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
    return { 'title': project_brains.Title,
             'url': project_brains.getURL(),
             'author': { 'home': member_url(author),
                         'userid': author },
             'date': project_brains.ModificationDate,
             }

def discussions2feed(message, args):
    member_url = args[0][0]
    author = message.getOwner().getUserName()
    return { 'title': message.Title,
             'url': message.absolute_url(),
             'author': { 'home': member_url(author),
                         'userid': author },
             'date': message.date
             }

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

        self.feed_types = []

        self.feed_types.append(Feed('Pages',
                                    ListFromCatalog(self._portal_type['pages'], self.project_path),
                                    ([self.catalog], {}),
                                    project2feed, ( [ self.memfolder_url ], {}) ),
                               )

        if self.has_mailing_lists:
            self.feed_types.append(Feed('Discussions',
                                        DiscussionList(self._portal_type['lists'], self.project_path),
                                        ([self.catalog], {}),
                                         discussions2feed, ( [ self.memfolder_url ], {}) ),
                                   )                                                             
    def snippet(self, feed):
        snip = self.context.unrestrictedTraverse('latest-snippet')
        snip.feedtitle = feed.title
        snip.items = feed.getfeeds()
        return snip()

    def feeds(self):
        feeds = []
        if self.has_blog:
            self.request['uri'] = '/'.join((self.context.absolute_url(),
                                            self._get_featurelet('blog')['url'],
                                            'feed'))
            blogfeed = self.context.unrestrictedTraverse('feedlist')
            feeds.append(blogfeed())
        feeds.extend( [ self.snippet(feed) for feed in self.feed_types ] )
        return feeds        

    def activity(self):
        f = ListFromCatalog(portal_type='Document', path=self.project_path)
        g = self.context.unrestrictedTraverse('latest-snippet')
        foo = g()

    def team_members(self):
        # XXX don't know if this is replicated elsewhere
        team = self.area.getTeams()
        assert len(team) == 1
        team = team[0]
        return [ self.member_info_for_member(member) for member in team.getMembers() ]
        
