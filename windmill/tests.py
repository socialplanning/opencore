from create_user import create_user
from create_user import create_user_cleanup
from windmill.authoring import WindmillTestClient

def test():
    client = WindmillTestClient(__name__)
    try:
        create_user(client)
    finally:
        create_user_cleanup()
