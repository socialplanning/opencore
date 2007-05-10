import difflib
from lxml import etree
import cgi
import re

def htmldiff(html1, html2):
    html1_tokens = tokenize(html1)
    html2_tokens = tokenize(html2)
    result = htmldiff_tokens(html1_tokens, html2_tokens)
    return ''.join(result).strip()

def htmldiff_tokens(html1_tokens, html2_tokens):
    s = difflib.SequenceMatcher()
    s.set_seq1(html1_tokens)
    s.set_seq2(html2_tokens)
    commands = s.get_opcodes()
    result = []
    for command, i1, i2, j1, j2 in commands:
        if command == 'equal':
            result.extend(expand_tokens(html2_tokens[j1:j2]))
            continue
        if command == 'insert' or command == 'replace':
            ins_tokens = expand_tokens(html2_tokens[j1:j2])
            merge_insert(ins_tokens, result)
        if command == 'delete' or command == 'replace':
            del_tokens = expand_tokens(html1_tokens[i1:i2])
            merge_delete(del_tokens, result)
    result = cleanup_delete(result)
    return result

def expand_tokens(tokens):
    for token in tokens:
        for pre in token.pre_tags:
            yield pre
        if token.trailing_whitespace:
            yield unicode(token) + ' '
        else:
            yield unicode(token)
        for post in token.post_tags:
            yield post

def merge_insert(chunks, result):
    unbalanced_start, balanced, unbalanced_end = split_unbalanced(chunks)
    result.extend(unbalanced_start)
    if result and not result[-1].endswith(' '):
        # Fix up the case where the word before the insert didn't end with 
        # a space
        result[-1] += ' '
    result.append('<ins>')
    if balanced and balanced[-1].endswith(' '):
        # We move space outside of </ins>
        balanced[-1] = balanced[-1][:-1]
    result.extend(balanced)
    result.append('</ins> ')
    result.extend(unbalanced_end)

class DEL_START:
    pass
class DEL_END:
    pass

class NoDeletes(Exception):
    pass

def merge_delete(chunks, result):
    result.append(DEL_START)
    result.extend(chunks)
    result.append(DEL_END)

def cleanup_delete(chunks):
    while 1:
        try:
            pre_delete, delete, post_delete = split_delete(chunks)
        except NoDeletes:
            break
        unbalanced_start, balanced, unbalanced_end = split_unbalanced(delete)
        locate_unbalanced_start(unbalanced_start, pre_delete, post_delete)
        locate_unbalanced_end(unbalanced_end, pre_delete, post_delete)
        doc = pre_delete
        if doc and not doc[-1].endswith(' '):
            # Fix up case where the word before us didn't have a trailing space
            doc[-1] += ' '
        doc.append('<del>')
        if balanced and balanced[-1].endswith(' '):
            # We move space outside of </del>
            balanced[-1] = balanced[-1][:-1]
        doc.extend(balanced)
        doc.append('</del> ')
        doc.extend(post_delete)
        chunks = doc
    return chunks

def split_unbalanced(chunks):
    start = []
    end = []
    tag_stack = []
    balanced = []
    for chunk in chunks:
        if not chunk.startswith('<'):
            balanced.append(chunk)
            continue
        endtag = chunk[1] == '/'
        name = chunk.split()[0].strip('<>/')
        if endtag:
            if tag_stack and tag_stack[-1][0] == name:
                balanced.append(chunk)
                name, pos, tag = tag_stack.pop()
                balanced[pos] = tag
            elif tag_stack:
                start.extend(tag for name, pos, tag in tag_stack)
                tag_stack = []
                end.append(chunk)
            else:
                end.append(chunk)
        else:
            tag_stack.append((name, len(balanced), chunk))
            balanced.append(None)
    start.extend(
        [chunk for name, pos, chunk in tag_stack])
    balanced = [chunk for chunk in balanced if chunk is not None]
    return start, balanced, end

def split_delete(chunks):
    try:
        pos = chunks.index(DEL_START)
    except ValueError:
        raise NoDeletes
    pos2 = chunks.index(DEL_END)
    return chunks[:pos], chunks[pos+1:pos2], chunks[pos2+1:]

def locate_unbalanced_start(unbalanced_start, pre_delete, post_delete):
    while 1:
        if not unbalanced_start:
            # We have totally succeded in finding the position
            break
        finding = unbalanced_start[0]
        finding_name = finding.split()[0].strip('<>')
        if not post_delete:
            break
        next = post_delete[0]
        if next is DEL_START or not next.startswith('<'):
            # Reached a word, we can't move the delete text forward
            break
        if next[1] == '/':
            # Reached a closing tag, can we go further?  Maybe not...
            break
        name = next.split()[0].strip('<>')
        if name == 'ins':
            # Can't move into an insert
            break
        assert name != 'del', (
            "Unexpected delete tag: %r" % next)
        if name == finding_name:
            unbalanced_start.pop(0)
            pre_delete.extend(post_delete.pop(0))
        else:
            # Found a tag that doesn't match
            break

def locate_unbalanced_end(unbalanced_end, pre_delete, post_delete):
    while 1:
        if not unbalanced_end:
            # Success
            break
        finding = unbalanced_end[-1]
        finding_name = finding.split()[0].strip('<>/')
        if not pre_delete:
            break
        next = pre_delete[-1]
        if next is DEL_END or not next.startswith('</'):
            # A word or a start tag
            break
        name = next.split()[0].strip('<>/')
        if name == 'ins' or name == 'del':
            # Can't move into an insert or delete
            break
        if name == finding_name:
            unbalanced_end.pop()
            post_delete.insert(0, pre_delete.pop())
        else:
            # Found a tag that doesn't match
            break

class token(unicode):

    def __new__(cls, text, pre_tags=None, post_tags=None, trailing_whitespace=False):
        obj = unicode.__new__(cls, text)

        if pre_tags is not None:
            obj.pre_tags = pre_tags
        else:
            obj.pre_tags = []

        if post_tags is not None:
            obj.post_tags = post_tags
        else:
            obj.post_tags = []

        obj.trailing_whitespace = trailing_whitespace

        return obj

    def __repr__(self):
        return 'token(%s, %r, %r)' % (unicode.__repr__(self), self.pre_tags, self.post_tags)

    def html(self):
        return ''.join(self.pre_tags) + self + ''.join(self.post_tags)

def tokenize(html):
    html = '<html><head></head><body><div>%s</div></body></html>' % html
    doc = etree.HTML(html)
    if doc is None:
        raise ValueError('HTML is malformed: %r' % html)
    body_el = doc.xpath('/html/body/div')[0]
    chunks = flatten_el(body_el, drop_tag=True)
    return fixup_chunks(chunks)

end_whitespace_re = re.compile(r'[ \t\n\r]$')

def fixup_chunks(chunks):
    tag_accum = []
    cur_word = None
    result = []
    chunks=list(chunks)
    for chunk in chunks:
        if is_word(chunk):
            if chunk.endswith(' '):
                chunk = chunk[:-1]
                trailing_whitespace = True
            else:
                trailing_whitespace = False
            if chunk.startswith('\000'):
                type, data, tag = chunk.split('\000')
                cur_word = tag_token(data, html_repr=tag, 
            cur_word = token(chunk, pre_tags=tag_accum, trailing_whitespace=trailing_whitespace)
            tag_accum = []
            result.append(cur_word)
        elif is_start_tag(chunk):
            tag_accum.append(chunk)
        elif is_end_tag(chunk):
            if tag_accum:
                tag_accum.append(chunk)
            else:
                assert cur_word, (
                    "Weird state, cur_word=%r, result=%r, chunks=%r of %r"
                    % (cur_word, result, chunk, chunks))
                cur_word.post_tags.append(chunk)
        else:
            assert(0)

    if not result:
        return [token('', pre_tags=tag_accum)]
    else:
        result[-1].post_tags.extend(tag_accum)

    return result


# All the tags in HTML that don't require end tags:
empty_tags = (
    'param', 'img', 'area', 'br', 'basefont', 'input',
    'base', 'meta', 'link', 'col')

def flatten_el(el, drop_tag=False):
    if not drop_tag:
        if el.tag == 'img':
            yield image_tag(el)
        elif el.tag == 'a' and el.attrib.get('href'):
            yield anchor_tag(el)
        else:
            yield start_tag(el)
    if el.tag in empty_tags and not el.text and not len(el):
        return
    start_words = split_words(el.text)
    for word in start_words:
        yield cgi.escape(word)
    for child in el:
        for item in flatten_el(child):
            yield item
    if not drop_tag:
        yield end_tag(el)
        end_words = split_words(el.tail)
        for word in end_words:
            yield cgi.escape(word)

def image_tag(el):
    return '\000image\000%s\000%s' % (el.attrib['src'], start_tag(el))

def anchor_tag(el):
    return '\000anchor\000%s\000%s' % (el.attrib['href'], start_tag(el))

def split_words(text):
    if not text or not text.strip():
        return []
    words = [w + ' ' for w in text.strip().split()]
    if not end_whitespace_re.search(text):
        words[-1] = words[-1][:-1]
    return words

start_whitespace_re = re.compile(r'^[ \t\n\r]')

def start_tag(el):
    return '<%s%s>' % (
        el.tag, ''.join(' %s="%s"' % (name, cgi.escape(value, True))
                        for name, value in el.attrib.items()))

def end_tag(el):
    if el.tail and start_whitespace_re.search(el.tail):
        extra = ' '
    else:
        extra = ''
    return '</%s>%s' % (el.tag, extra)

def is_word(tok):
    return not tok.startswith('<')

def is_end_tag(tok):
    return tok.startswith('</')

def is_start_tag(tok):
    return tok.startswith('<') and not tok.startswith('</')

if __name__ == '__main__':
    import doctest
    doctest.testfile('test_htmldiff2.txt')
