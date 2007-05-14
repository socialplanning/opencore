from zope.interface import Interface, Attribute


class IOpenTeam(Interface):
    """
    Interface provided by OpenTeam objects.

    XXX: TeamSpace needs to be updated to use Z3 interfaces so we can
    subclass from those.
    """
    def getProject():
        """Returns the associated project object.

        Tried to make this a python property, but was getting
        attribute errors from the ProjectInfoView.project method.
        """
