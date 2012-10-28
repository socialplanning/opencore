"""
This file downloaded from https://github.com/dpapathanasiou/python-recaptcha on 2012/10/28 

The MIT License (MIT)
Copyright (c) 2012 Denis Papathanasiou

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included
in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.
"""

import urllib, urllib2

recaptcha_private_key = '...[your private key goes here]...'

recaptcha_server_name = 'http://www.google.com/recaptcha/api/verify'

def to_bytestring (s):
    """Convert the given unicode string to a bytestring, using the standard encoding,
    unless it's already a bytestring"""
    if s:
        if isinstance(s, str):
            return s
        else:
            return s.encode('utf-8')

def check (client_ip_address, recaptcha_challenge_field, recaptcha_response_field):
    """Return the recaptcha reply for the client's challenge responses"""
    params = urllib.urlencode(dict(privatekey=recaptcha_private_key,
                                   remoteip=client_ip_address,
                                   challenge=recaptcha_challenge_field,
                                   response=to_bytestring(recaptcha_response_field)))
    data = None
    try:
        f = urllib2.urlopen(recaptcha_server_name, params)
        data = f.read()
        f.close()
    except HTTPError:
        pass
    except URLError:
        pass
    return data

def confirm (client_ip_address, recaptcha_challenge_field, recaptcha_response_field):
    """Return True/False based on the recaptcha server's reply"""
    result = False
    reply = check (client_ip_address, recaptcha_challenge_field, recaptcha_response_field)
    if reply:
        if reply.lower().startswith('true'):
            result = True
    return result
