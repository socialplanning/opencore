from zope.component import adapts
from zope.interface import implements

from Products.CMFCore.utils import getToolByName

from opencore.i18n import _

from opencore.interfaces import IOpenSiteRoot
from opencore.member.interfaces import ICreateMembers

class _FakeRequest(object):
    def __init__(self, fields=None):
        form = dict()
        form.update(fields)
        self.form = form

    def __getattr__(self, attr):
        """
        because i'm lazy
        """
        try:
            return getattr(self.form, attr)
        except AttributeError:
            return getattr(object, attr) 

    def __getitem__(self, item):
        """
        just in case
        """
        return self.form.__getitem__(item)

class MemberFactory(object):
    adapts(IOpenSiteRoot)
    implements(ICreateMembers)
    
    def __init__(self, context):
        self.context = context

    @property
    def _membertool(self):
        return getToolByName(self.context, "portal_memberdata")

    @property
    def _validation_member(self):
        return self._membertool._validation_member

    def validate(self, fields):
        errors = {}
        request = _FakeRequest(fields)
        errors = self._validation_member.validate(REQUEST=request,
                                                  errors=errors,
                                                  data=1, metadata=0)
        pw, pw_ = (request.form.get("password"),
                   request.form.get("confirm_password"))
        if not pw and not pw_:
            errors['password'] = _(u'no_password', u'Please enter a password')
        return errors
