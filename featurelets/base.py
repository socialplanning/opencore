from OFS.interfaces import IObjectManager

class BaseFeaturelet(object):
    """
    Abstract base class for featurelet objects.
    """
    _required_interfaces = (IObjectManager,)

    def _checkForRequiredInterfaces(self, obj):
        """
        Checks to see if the obj implements or can be adapted to all
        of the featurelet's required interfaces.
        """
        for iface in (IFeatureletSupporter,) + \
                self.getRequiredInterfaces():
            # just let adaptation raise an exception if necessary
            iface(obj)

    def getRequiredInterfaces(self):
        """
        See IFeaturelet.
        """
        return self._required_interfaces

    def deliverPackage(self, obj):
        """
        See IFeaturelet.
        """
        self._checkForRequiredInterfaces(obj)
