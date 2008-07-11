from lib.utils import logger

class Suite(object):
    """
    Base class for windmill test suites.
    """
    def __init__(self, client):
        self.client = client

    def run(self):
        try:
            logger.info("Starting '%s' suite" % self.name)
            self._run()
        finally:
            logger.info("Cleaning up '%s' suite." % self.name)
            self.cleanup()

