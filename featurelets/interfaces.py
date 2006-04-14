from zope.interface import Interface, Attribute

class IFeaturelet(Interface):
    """
    Marks a featurelet that can be plugged in to any IFeatureletSupporter.
    """

    id = Attribute("id")
    
    def getConfigView():
        """
        Returns a view object responsible for exposing the
        configuration options for the featurelet.  This configures the
        'package' that the featurelet provides to the featurelet
        supporter when deliverPackage is called.
        """

    def getRequiredInterfaces():
        """
        Returns a tuple of any interfaces (additional to
        IFeatureletSupporter) that this featurelet requires of its
        supporters.  Featurelet supporters may either implement or
        singly adapt to each of the required interfaces.
        """

    def deliverPackage(obj):
        """
        Performs the actual installation of the functionality
        'package' of the featurelet into an object.  Raises an
        exception if the object does not implement or adapt to
        IFeatureletSupporter of any of the required interfaces.

        If the featurelet is already installed, the featurelet will
        only install any differences btn the supporters stored
        featurelet description and the description that the featurelet
        has currently.

        Returns the featurelet description as it was installed.
        """

    def removePackage(obj):
        """
        Removes the featurelet's functionality from the obj.  This is
        potentially destructive (it will remove any objects that the
        featurelet created, for instance) so it should be used with
        care.
        """

class IFeatureletSupporter(Interface):
    """
    Marks a featurelet supporter that can accomodate IFeaturelets.
    """

    def getInstalledFeatureletIds():
        """
        Returns the ids of all installed featurelets; retrieved from
        the information the featurelets place in the featurelet
        annotation.
        """

    def getFeatureletDescriptor(id):
        """
        Returns the featurelet descriptor for the provided featurelet
        id, or None if the featurelet isn't installed.
        """

    def installFeaturelet(featurelet):
        """
        Installs the provided featurelet into the supporter. 
        """

    def removeFeaturelet(featurelet):
        """
        Uninstalls the provided featurelet, if it is installed.
        """
