from basic import BasicSuite
from lib.utils import logger
from windmill.authoring import WindmillTestClient

suite_classes = [BasicSuite]

def test():
    client = WindmillTestClient(__name__)
    for klass in suite_classes:
        suite = klass(client)
        suite.run()
    logger.info("Finished with test run")
