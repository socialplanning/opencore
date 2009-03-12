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
            self.mock_attrs[attr] = self.__class__(new_name)
        return self.mock_attrs[attr]

class ConfigMock(Mock):

    def __init__(self, *args, **kw):
        self._dummy_values = {}

    def _set(self, option, value):
        self._dummy_values[option] = value

    def get(self, option, default=None):
        return self._dummy_values.get(option, default)

class HTTPMock(Mock):
    """ 
    A mock object for simulating httplib2.Http objects
    """
    _resp_content = []

    class MockResponse(object):
        def __init__(self, status=200):
            self.status = status # <--- httplib2 response codes are strings
        def get(self, key, default=None):
            value = getattr(self, key, default)
            if value != default:
                # response codes are strings retrieved using dict API
                value = str(value)
            return value
        def __getitem__(self, key, default=None):
            return self.get(key, default)
    
    @classmethod
    def add_to_response_content(cls, content, status=200):
        response = cls.MockResponse(status)
        cls._resp_content.append((response, content))

    @property
    def resp_content(self):
        if HTTPMock._resp_content:
            ret = HTTPMock._resp_content[0]
            HTTPMock._resp_content = HTTPMock._resp_content[1:]
            return ret
        return ((self.MockResponse(200), "Mock request succeeded!"))
    
    def __call__(self, *args, **kw):
        base_response = Mock.__call__(self, *args, **kw)
        if self.mock_name.endswith("request"):
            response, content = self.resp_content
            return (response, content)
        return base_response

    def __repr__(self):
        return '<HTTPMock %s %s>' % (hex(id(self)), self.mock_name)
    

if __name__ == '__main__':
    import doctest
    doctest.testmod()
    
