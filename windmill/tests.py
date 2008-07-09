from create_user import create_user
from windmill.authoring import WindmillTestClient

def test():
    client = WindmillTestClient(__name__)
    create_user(client)
