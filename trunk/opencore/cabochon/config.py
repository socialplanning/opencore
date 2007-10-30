import os

event_server = "http://localhost:24532"

#fixme: this should probably be something like /var/...
event_queue_directory = os.path.join(os.path.abspath(os.path.dirname(__file__)), "eq")

cabochon_username = "topp"
cabochon_password = "secret"
