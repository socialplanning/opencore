import re

def strip_escapes(string):
    """remove HTML escape characters from a string and replace with unicode"""

    def replace(escapeseq):
        import pdb;  pdb.set_trace()
        return ("\\u%x" % int(escapeseq[2:-1])).decode("unicode_escape")
    
    regex = r'&#[0-9]+;'
    matches = re.findall(regex, string)
    rest = re.split(regex, string)

    retval = [ unicode(rest[0]) ]

    for match, string in zip(matches, rest[1:]):
        retval.extend([ replace(match), unicode(string) ])

    return u''.join(retval)
