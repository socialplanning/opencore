from zope.component import adapts
from zope.interface import implements
from zope.event import notify
from zope.app.event.objectevent import ObjectCreatedEvent

from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import transaction_note

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

    def create(self, fields):
        # create a member in portal factory
        mdc = self._membertool
        pf = mdc.portal_factory

        #00 pythonscript call, move to fs code
        id_ = self.context.generateUniqueId('OpenMember')

        mem_folder = pf._getTempFolder('OpenMember')
        mem = mem_folder.restrictedTraverse('%s' % id_)

        # now we have mem, a temp member. create him for real.
        request = _FakeRequest(fields)
        mem_id = fields.get('id')
        mem = pf.doCreate(mem, mem_id)
        transaction_note('Created %s with id %s in %s' % \
                             (mem.getTypeInfo().getId(),
                              mem_id,
                              self.context.absolute_url()))

        # post-creation setup
        result = mem.processForm(REQUEST=request)
        # what does result look like? what do we do with it?
        # and shouldn't we process form BEFORE we finalize creation?
        notify(ObjectCreatedEvent(mem)) #is this necessary here?
        mem.setUserConfirmationCode()

        return mem
