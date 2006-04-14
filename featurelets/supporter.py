from persistent.mapping import PersistentMapping

from zope.interface import implements
from zope.app.annotation.interfaces import IAnnotations

from interfaces import IFeatureletSupporter

class FeatureletSupporter(object):
    """
    Adapts from IAnnotatable to IFeatureletSupporter.
    """

    implements(IFeatureletSupporter)
    annotations_key = "featurelets"

    def __init__(self, context):
        self.context = context
        annotations = IAnnotations(context)
        key = self.annotations_key
        if not annotations.has_key(key):
            annotations[key] = PersistentMapping()
        self.storage = annotations[key]

    def getInstalledFeatureletIds(self):
        """
        See IFeatureletSupporter.
        """
        return self.storage.keys()

    def getFeatureletDescriptor(self, id):
        """
        See IFeatureletSupporter.
        """
        return self.storage.get(id)

    def installFeaturelet(self, featurelet):
        """
        See IFeatureletSupporter.
        """
        info = featurelet.deliverPackage(self.context)
        self.storage[featurelet.id] = info

    def removeFeaturelet(self, featurelet):
        """
        See IFeatureletSupporter.
        """
        if self.storage.has_key(featurelet.id):
            featurelet.removePackage(self.context)
            self.storage.pop(featurelet.id)
