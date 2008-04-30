# topnav view tests

import re

def parse_topnav_context_menu(contextmenu_html):
    """convenience method to parse topnav list items"""

    lis = [] # list of list item dicts, contains 'selected'
    as = [] # list of link dicts: contains 'href' and 'name'

    li_pattern = re.compile('<li class="([^"]*)')
    a_pattern = re.compile('<a href="([^"]*)">([^<]*)')

    # This is pretty fragile, should we use lxml or some such?
    for line in contextmenu_html.split('\n'):
        line = line.strip()
        if line.startswith('<li'):
            li_match = li_pattern.search(line)
            if li_match:
                selected = li_match.group(1)
            else:
                selected = False
            lis.append(dict(selected=selected))
        elif line.startswith('<a'):
            a_match = a_pattern.search(line)
            if a_match:
                href, name = a_match.group(1), a_match.group(2)
                as.append(dict(href=href, name=name))

    assert len(lis) == len(as)
    return lis, as
