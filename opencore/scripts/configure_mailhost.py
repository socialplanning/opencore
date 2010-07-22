from opencore.utils import setup
import transaction

app = setup(app)

mh = app.openplans.MailHost

if not mh.smtp_host:
    mh.smtp_host = "localhost"
    mh.smtp_port = 25
    transaction.commit()
