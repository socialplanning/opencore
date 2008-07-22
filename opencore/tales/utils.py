from topp.utils.pretty_date import prettyDate
from opencore.project.utils import project_noun
from zope.traversing.interfaces import IPathAdapter
from zope import interface
from zope import component

class OpencoreTales(object):
    component.adapts(interface.Interface)
    interface.implements(IPathAdapter)

    def __init__(self, context):
        if callable(context):
            self.context = context()
        else:
            self.context = context

    def pretty_date(self):
        return prettyDate(self.context)

    def project_noun(self):
        return project_noun()
