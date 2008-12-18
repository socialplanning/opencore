# creates the az translation from the en po file
# az translation has all msgstr set to the corresponding msgid

import sys
import os


header = """msgid ""
msgstr ""
"Project-Id-Version: opencore\\n"
"POT-Creation-Date: \\n"
"PO-Revision-Date: 2007-11-08 16:24-0500\\n"
"Last-Translator: \\n"
"Language-Team: The Open Planning Project\\n"
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=utf-8\\n"
"Content-Transfer-Encoding: 8bit\\n"
"X-Poedit-Language: Azerbaijani\\n"
"X-Poedit-Country: AZERBAIJAN\\n"
"Domain: opencore\\n"
"Language-Code: az\\n"
"Language-Name: Azerbaijani\\n"
"""



def create_az(file_name=None, file_name2=None):
    # step through the en file starting at the bottom of the header
    # copying line by line yet setting msgstr equal to the preceding
    # msgid
    cwd = os.path.dirname(os.path.abspath(__file__))
    if file_name == None:
        file_name = os.path.join(cwd, 'en', 'LC_MESSAGES', 'opencore.po')
    if file_name2 == None:
        file_name2 = os.path.join(cwd, 'az', 'LC_MESSAGES', 'opencore.po')

    f1 = open(file_name, 'r')
    f2 = open(file_name2, 'w')

    import re
    msgid_re = re.compile(r'msgid\s"(.*)"')

    def get_msgid(line):
        found = msgid_re.search(line)
        if found:
            return found.group(1)
        else:
            return None

    f2.write(header)
    f2.flush()

    in_header = True
    msgid = None

    for line in f1:
        msgid = get_msgid(line) or msgid
        if in_header:
            # Skip the header, we wrote our own.
            if msgid:
                in_header = False
            elif line.startswith('#'):
                in_header = False
                f2.write(line)
            else:
                continue
        if 'msgstr' in line and not line.startswith('#'):
            assert msgid
            f2.write('msgstr "%s"' % msgid)
            msgid = None  # Make sure we use each msgid only once.
        else:
            f2.write(line)
    return file_name2

if __name__ == '__main__':
    created = create_az(*sys.argv[1:3])
    print "Created", created, "OK"
