# (c) 2006 Ian Bicking and contributors
# Licensed under the MIT license: http://www.opensource.org/licenses/mit-license.php

r"""
minimock is a simple library for doing Mock objects with doctest.
When using doctest, mock objects can be very simple.

Here's an example of something we might test, a simple email sender::

    >>> import smtplib
    >>> def send_email(from_addr, to_addr, subject, body):
    ...     conn = smtplib.SMTP('localhost')
    ...     msg = 'To: %s\nFrom: %s\nSubject: %s\n\n%s' % (
    ...         to_addr, from_addr, subject, body)
    ...     conn.sendmail(from_addr, [to_addr], msg)
    ...     conn.quit()

Now we want to make a mock ``smtplib.SMTP`` object.  We'll have to
inject our mock into the ``smtplib`` module::

    >>> smtplib.SMTP = Mock('smtplib.SMTP')
    >>> smtplib.SMTP.mock_returns = Mock('smtp_connection')

Now we do the test::

    >>> send_email('ianb@colorstudy.com', 'joe@example.com',
    ...            'Hi there!', 'How is it going?')
    Called smtplib.SMTP('localhost')
    Called smtp_connection.sendmail(
        'ianb@colorstudy.com',
        ['joe@example.com'],
        'To: joe@example.com\nFrom: ianb@colorstudy.com\nSubject: Hi there!\n\nHow is it going?')
    Called smtp_connection.quit()

Voila!  We've tested implicitly that no unexpected methods were called
on the object.  We've also tested the arguments that the mock object
got.  We've provided fake return calls (for the ``smtplib.SMTP()``
constructor).  These are all the core parts of a mock library.  The
implementation is simple because most of the work is done by doctest.
"""

class Mock(object):

    def __init__(self, name):
        self.mock_name = name
        self.mock_returns = None
        self.mock_attrs = {}

    def __repr__(self):
        return '<Mock %s %s>' % (hex(id(self)), self.mock_name)

    def __call__(self, *args, **kw):
        parts = [repr(a) for a in args]
        parts.extend(
            '%s=%r' % (items) for items in sorted(kw.items()))
        msg = 'Called %s(%s)' % (self.mock_name, ', '.join(parts))
        if len(msg) > 80:
            msg = 'Called %s(\n    %s)' % (
                self.mock_name, ',\n    '.join(parts))
        print msg
        return self.mock_returns

    def __getattr__(self, attr):
        if attr not in self.mock_attrs:
            if self.mock_name:
                new_name = self.mock_name + '.' + attr
            else:
                new_name = attr
            self.mock_attrs[attr] = Mock(new_name)
        return self.mock_attrs[attr]

    
if __name__ == '__main__':
    import doctest
    doctest.testmod()
    
