A member should implement IOpenMember::
    >>> mem = self.portal.portal_memberdata.m1
    >>> mem
    <OpenMember at /plone/portal_memberdata/m1>
    >>> from opencore.member.interfaces import IOpenMember
    >>> IOpenMember.providedBy(mem)
    True

