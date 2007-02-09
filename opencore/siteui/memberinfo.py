from Products.CMFCore.utils import getToolByName 
from Products.Five import BrowserView
from Products.remember.interfaces import IReMember
from interfaces import IMemberFolder
from interfaces import IMemberInfo
from memojito import memoizedproperty, memoize
from zope.interface import implements


class MemberInfoView(BrowserView):
    implements(IMemberInfo)

    def __init__(self, context, request):
        self._context = (context,)
        self.request = request
        self.mtool = getToolByName(self.context(), 'portal_membership')

    def context(self):
        return self._context[0]

    def interfaceInAqChain(self, iface):
        chain = self.context().aq_chain
        match = None
        for item in chain:
            if iface.providedBy(item):
                match = item
                break
        return match

    @memoizedproperty
    def member_folder(self):
        return self.interfaceInAqChain(IMemberFolder)

    @memoizedproperty
    def member_object(self):
        return self.interfaceInAqChain(IReMember)

    @memoizedproperty
    def member(self):
        member = None
        mf = self.member_folder
        if mf is not None:
            # XXX we shouldn't rely on the folder id matching the user id;
            #     maybe store the member id in an annotation on the folder?
            member = self.mtool.getMemberById(mf.getId())
        elif self.member_object is not None:
            member = self.member_object
        return member

    @memoizedproperty
    def personal_folder(self):
        mem_id = self.mtool.getAuthenticatedMember().getId()
        return self.mtool.getHomeFolder(mem_id)

    @memoizedproperty
    def inMemberObject(self):
        return self.member_object is not None

    @memoizedproperty
    def inSelf(self):
        return self.inMemberObject and self.member_object == \
               self.mtool.getAuthenticatedMember()

    @memoizedproperty
    def inMemberArea(self):
        return self.member_folder is not None

    @memoizedproperty
    def inPersonalArea(self):
        return self.inMemberArea and self.member_folder == self.personal_folder
