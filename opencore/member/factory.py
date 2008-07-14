from zope.component import adapts
from zope.interface import implements
from zope.event import notify
from zope.app.event.objectevent import ObjectCreatedEvent

from AccessControl.SecurityManagement import getSecurityManager
from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.SecurityManagement import setSecurityManager
from AccessControl.SpecialUsers import system as system_user
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

    def validate(self, request):
        """
        Delegates to AT validation on a shared persistent reference
        member object.
        """
        # XXX changes to AT in Plone 3 have made this convenience hack
        # for using AT's validation machinery way more painful.  we
        # really need to replace this with a different validation
        # mechanism. (ra)

        validation_member = self._validation_member

        # XXX we temporarily become a Manager user b/c we have to have
        # write privs on a field before AT will perform the validation
        orig_sec_mgr = getSecurityManager()
        app = validation_member.getPhysicalRoot()
        user = system_user
        newSecurityManager(request, user)
        errors = {}
        request = _FakeRequest(request.form) # why fake request? (ra)
        
        errors = validation_member.validate(REQUEST=request,
                                            errors=errors,
                                            data=1, metadata=0)

        # return to being the original user
        setSecurityManager(orig_sec_mgr)

        pw, pw_ = (request.form.get("password"),
                   request.form.get("confirm_password"))
        if not pw and not pw_:
            errors['password'] = _(u'no_password', u'Please enter a password')

        if not errors.has_key('password'):
            # XXX now we have to (re)validate the password, b/c being a
            # Manager meant the password length check was too lenient
            regtool = getToolByName(self.context, 'portal_registration')
            pwerror = regtool.testPasswordValidity(pw, pw_)
            if pwerror is not None:
                errors['password'] = pwerror
        
        return errors

    def create(self, fields):
        # create a member in portal factory
        # i don't think this is really necessary any more. -egj
        pf = self._membertool.portal_factory

        #00 pythonscript call, move to fs code
        id_ = self.context.generateUniqueId('OpenMember')

        mem_folder = pf._getTempFolder('OpenMember')
        mem = mem_folder.restrictedTraverse('%s' % id_)

        # now we have mem, a temp member. create him for real.
        mem_id = fields.get('id')
        mem = pf.doCreate(mem, mem_id)
        transaction_note('Created %s with id %s in %s' % \
                             (mem.getTypeInfo().getId(),
                              mem_id,
                              self.context.absolute_url()))

        # post-creation setup
        result = mem.processForm(values=fields)
        # what does result look like? what do we do with it?
        # and shouldn't we process form BEFORE we finalize creation?
        notify(ObjectCreatedEvent(mem))
        mem.setUserConfirmationCode()

        return mem
