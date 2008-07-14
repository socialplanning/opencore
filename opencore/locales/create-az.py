# creates the az translation from the en po file
# az translation has all msgstr set to the corresponding msgid

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

# step through the en file starting at the bottom of the header
# copying line by line yet setting msgstr equal to the preceding
# msgid

import sys
import os.path
if len(sys.argv)==3:
    file_name = sys.argv[1]
    file_name2 = sys.argv[2]
else:
    file_name = os.path.join('en', 'LC_MESSAGES', 'opencore.po')
    file_name2 = os.path.join('az', 'LC_MESSAGES', 'opencore.po')

f1 = open(file_name)
f2 = open(file_name2, 'w')

for line in f1:
    if '#' in line:
        break

f2.write(header)
f2.write(line)
for line in f1:
    if 'msgid' in line:
        msgid = line.split()[1]
    if 'msgstr' in line and not line.startswith('#'):
        f2.write('msgstr ' + msgid)
    else:
        f2.write(line)

