from basic import basic_suite
from basic import basic_suite_cleanup
from lib.utils import logger
from windmill.authoring import WindmillTestClient

def test():
    client = WindmillTestClient(__name__)
    try:
        basic_suite(client)
    finally:
        basic_suite_cleanup()
    logger.info("Finished with test run")
