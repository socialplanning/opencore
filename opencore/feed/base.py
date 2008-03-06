class BaseFeedAdapter(object):
    """Useful base class that provides most common functionality.
       Context needs to provide dublin core.

       Implementations only have to provide the items iterable"""

    def __init__(self, context):
        self.context = context

    @property
    def title(self):
        return '%s Opencore Feed' % self.context.Title()

    @property
    def description(self):
        return 'Opencore Feed for %s: %s' % (self.context.Title(),
                                             self.context.Description())

    @property
    def link(self):
        return self.context.absolute_url()

    language = 'en-us'

    @property
    def pubDate(self):
        return self.context.modified()

    @property
    def author(self):
        return self.context.Creator()
