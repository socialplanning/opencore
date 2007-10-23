import logging

class Base(object):
    """ view class stub """
    
    def __init__(self, context, request):
        self._context = (context,)
        self.request = request

    @property
    def context(self):
        return self._context[0]

    @property
    def logger(self):
        return logging.getLogger(LOG)


