function WickedLinkValidator(editor) {
  this.editor = editor;
};

WickedLinkValidator._pluginInfo = {
  name          : "WickedLinkValidator",
  version       : "0.1",
  developer     : "OpenCore developers",
  developer_url : "http://www.coactivate.org/projects/opencore",
  c_owner       : "Ethan Jucovy",
  license       : "htmlarea"
};

WickedLinkValidator.prototype.onExecCommand = function(cmdID, UI, param) {
  if( cmdID != "createlink" ) return false;
  var error = WickedLinkValidator.checkWickedLinks(this.editor,
						   param, Xinha._lc);
  if( error ) {
    // if the validator finds a matching ((wicked link))
    // it will return an error message
    // so we'll pop it up for the user, and then abort further events
    alert(error);
    return true;
  }
  return false;
};


WickedLinkValidator.checkWickedLinks = function(editor, a, _lc) {
    var selection = editor.getSelection();
    var range = editor.createRange(selection);

    // We need to copy the selection text before we monkey with the DOM...
    selection_text = range.toString ? range.toString() : range.text;

    // We will use these variable to abstract away how much it sucks to work
    // with Internet Explorer text ranges
    var startContainer = null, startOffset = 0, endContainer = null, endOffset = 0;

    if (range.startContainer) {
        // We have W3C range support, and the ability to directly access the nodes
        // before and after the range
        startContainer = range.startContainer;
        startOffset = range.startOffset;
        endContainer = range.endContainer;
        endOffset = range.endOffset;
    } else {
        // There is no W3C range support, so we have to work with legacy IE TextRanges.  In
        // order to find the start and end nodes, we will have to insert an element into the DOM,
        // and then look for the adjacent node.  The only problem with this is that when we have
        // a part of a text node selected, we will split the text node into two, breaking the
        // offsets.  After calculating our offsets, we will have to rejoin any text nodes that we
        // have split, understanding that we may have split one text node into three pieces.
        var rejoinLeft = null, rejoinRight = null;

        // For absolute security, we should generate a random ID, check to see if it exists, and if not,
        // regenerate another.  However, if anyone is using this id below by simple chance, I'll be a monkey's
        // uncle, and you can make me code the replacement function.
        var hopefully_unique_id = 'vnairneiwnvuihiudhjSDNfoi3u80v__ceqwg898f734j';

        // We make a copy of the original range so that we can collapse it down into just the left edge.
        var edgeLeft = range.duplicate();
        edgeLeft.collapse(true); // Collapse left
        edgeLeft.pasteHTML('<span id="' + hopefully_unique_id + '"></span>');

        // At this point, you'd think we could just perform a document.getElementById() and we could move on.
        // Unfortunately, you'd be wrong.  Elements inserted using the pasteHTML method of an IE TextRange can't
        // be looked up reliably by ID, so we have to access the parent element of the range, and look though
        // after that element for our node.  Unfortunately, TextRange.parentElement() is not guaranteed to return
        // a parent of the range, it may just return a node that is to left of the range in the DOM.
        var find = WickedLinkValidator.lookForwardById(edgeLeft.parentElement(), hopefully_unique_id);

        // If the insertion is in the middle of two text nodes, that means we split a text node
        // with the HTML insertion.  We will record the offset, and mark the node to be recombined
        // after successful retrieval of the ending offset.
        if (find.previousSibling && find.nextSibling &&
            (find.previousSibling.nodeType == 3) && (find.nextSibling.nodeType == 3)) {

          startOffset = find.previousSibling.data.length;
          rejoinLeft = find.nextSibling;

          // Since the previousSibling is going to be deleted below, we have to point startContainer
          // to the half of the text node that will not be removed.
          startContainer = rejoinLeft;
        } else {
            // If there is no sibling to the left, the next node to the left is the parent.
            startContainer = null == find.previousSibling ? find.parentNode : find.previousSibling;
        }

        // Clean up afer ourselves and remove the bogus element,
        find.parentNode.removeChild(find);

        // Youpi!  We get to repeat all of this, only slightly different for the right edge.
        edgeRight = range.duplicate();
        edgeRight.collapse(false); // Collapse right
        edgeRight.pasteHTML('<span id="' + hopefully_unique_id + '"></span>');

        // Find the inserted element.
        find = WickedLinkValidator.lookForwardById(edgeLeft.parentElement(), hopefully_unique_id);

        // The text node may have been split, so mark for repairing.
        if (find.previousSibling && find.nextSibling &&
            (find.previousSibling.nodeType == 3) && (find.nextSibling.nodeType == 3)) {

            // we split a text node by inserting here, so we need to restore the text node.
          endOffset = find.previousSibling.data.length ;
          rejoinRight = find.previousSibling;
          endContainer = rejoinRight;
          if (rejoinLeft && rejoinLeft == rejoinRight) {
              // We split a single text node into three pieces
              endOffset += startOffset;
          }
        } else {
            // If this is a selection to the end of the document, I'm pretty sure this algorithm will fail, because there is no endContainer...
            for (endContainer = find; null == endContainer.nextSibling && endContainer.parentNode != null; endContainer = endContainer.parentNode) {
                // Just navigate the tree to find the next sibling
            }

            // At this point, either we have a nextSibling, or this is the root node
            if (endContainer.nextSibling) {
                endContainer = endContainer.nextSibling;
            }
        }

        // Clean up after ourselves again
        find.parentNode.removeChild(find);

        // Now that we've safely retrieved the offsets, we can rejoin any split text nodes
        if (rejoinLeft != null) {
            rejoinLeft.data = rejoinLeft.previousSibling.data + rejoinLeft.data;
            rejoinLeft.parentNode.removeChild(rejoinLeft.previousSibling);
        }
        if (rejoinRight != null) {
            rejoinRight.data = rejoinRight.data + rejoinRight.nextSibling.data;
            rejoinRight.parentNode.removeChild(rejoinRight.nextSibling);
        }
    }

    // This algorithm is going to have a lot of explanation, because it is not
    // at all obvious.  I hope that's just a byproduct of the fact that we have
    // to do tree traversal and we have complicated link rules, not because
    // I've written illegible code. This algorithm is very dependant on
    // Wicked's processing of wiki links, as it uses Wicked rules to determine
    // whether or not a link is active.  Important things to know about Wicked
    // link processing:
    //
    // 1) Wicked links can not be nested
    // 2) Nested Wicked links are treated as plain text
    // 3) Close brackets '))' that lead the text are just plain brackets
    // 4) Unclosed trailing open brackets '((' are also just plain brackets
    //
    // A byproduct of all this is that at any given point, the last set of
    // brackets ('((' or '))') determine the link state.  If they are open
    // brackets, we are potentially in a link (unless there are no closing
    // brackets), and if they are close brackets, we are not currently in a
    // link.
    //
    // As such, our algorithm is as follows:
    // Are we in a link state because of open brackets before the selection?
    //     If so, check for close brackets in or after the selection.
    // If not, are we in a link state because there are open brackets in the selection?
    //     If so, check for a valid Wicked link in the selection, or close brackets
    //     trailing the selection.
    //
    // Finally, I'd like to explain the tree traversal.  For a node to be
    // considered as after the current node, it has to be either a child of the
    // current node, or a sibling (and it's children) to the right of the
    // current node, or a sibling (and it's children) to the right of it's
    // parents.
    // Nodes that are before the current node or siblings (and their children)
    // to the left, or siblings (and their children) to the left of parents.
    //
    // In order to visit all nodes in a direction, we have to perform two
    // different operations.  The first is an up traversal, where we process
    // the current node and all of it's parents in order to find siblings in
    // the given direction.  The second is a down traversal, where for each
    // node not in the direct chain of parents, we travers all of its children.

    // In order to be sure we don't check Wicked links in comments, we have
    // to only process the selection text.  For W3C ranges, we use the toString()
    // method, and the text property for IE

    var re_closelink = new RegExp (/\)\)+/), // "))"
        re_openlink = new RegExp (/\(\(+/), // "(("
        re_wickedlink = new RegExp (/\(\(+.*\)\)+/); // "(( Something ))"
    if (WickedLinkValidator.search_up(startContainer, 'left', startOffset) == 'open') {
        if ((selection_text.search(re_closelink) >= 0) || (WickedLinkValidator.search_up(endContainer, 'right', endOffset))) {

            return _lc('Cannot create a link inside of a wiki link');
        }
    } else if ((selection_text.search(re_openlink) >= 0) &&
        ((selection_text.search(re_wickedlink) >= 0) || (WickedLinkValidator.search_up(endContainer, 'right', endOffset)))) {

        return _lc('Cannot create a link inside of a wiki link');
    }
};


WickedLinkValidator.search_up = function(elt, direction, offset) {
    var dir_property = 'nextSibling';
    if (direction == 'left') {
        dir_property = 'previousSibling';
    }
    // If the current node is a text node (which can only happen on the very first call, since text nodes
    // can't have children), we search the portion of it that is to the left or right of the selection.
    // Otherwise, we search all siblings in the given direction, and continue doing so until we hit the root.
    // This search will stop at the top of the iframe, and not continue into the parent document.
    for (var node = elt.nodeType == 3 ? elt : elt[dir_property]; node != null; node = node[dir_property]) {
        // 3 is text node
        if (node.nodeType == 3) {
            if (direction == 'left') {
                var nv = offset != undefined ? node.nodeValue.substring(0, offset) : node.nodeValue;
                var result = nv.match(/\(\(+|\)\)+/g);
                if (result && result.length > 0) {
                    return result[result.length-1].charAt(0) == '(' ? 'open' : 'closed';
                }
            } else {
                var nv = offset != undefined ? node.nodeValue.substring(offset, node.nodeValue.length-1) : node.nodeValue;
                var result = nv.match(/\)\)+/g);
                if (result && result.length > 0) {
                    return 'closed'
                }
            }
        // Node 1 is an element
        } else if (node.nodeType == 1) {
            down = WickedLinkValidator.search_down(node, direction);
            if ((down == 'open') || (down == 'closed')) {
                return down;
            }
        }
    }
    if (elt.parentNode) {
        return WickedLinkValidator.search_up(elt.parentNode, direction);
    }
}

WickedLinkValidator.search_down = function(elt, direction) {
    var child_property = 'firstChild';
    var dir_property = 'nextSibling';
    if (direction == 'left') {
        dir_property = 'previousSibling';
        child_property = 'lastChild';
    }
    for (var node = elt[child_property]; node != null; node = node[dir_property]) {
        // 3 is text node
        if (node.nodeType == 3) {
            if (direction == 'left') {
                var result = node.nodeValue.match(/\(\(+|\)\)+/g);
                if (result && result.length > 0) {
                    return result[result.length-1].charAt(0) == '(' ? 'open' : 'closed';
                }
            } else {
                var result = node.nodeValue.match(/\)\)+/g);
                if (result && result.length > 0) {
                    return 'closed'
                }
            }
        } else if (node.nodeType == 1) {
            down = WickedLinkValidator.search_down(node, direction);
            if ((down == 'open') || (down == 'closed')) {
                return down;
            }
        }
    }
}

WickedLinkValidator.lookForwardById = function(elt, id, already_called) {
    // If the current node is a text node (which can only happen on the very first call, since text nodes
    // can't have children), we search the portion of it that is to the left or right of the selection.
    // Otherwise, we search all siblings in the given direction, and continue doing so until we hit the root.
    // This search will stop at the top of the iframe, and not continue into the parent document.
    for (var node = already_called ? elt.nextSibling : elt; node != null; node = node.nextSibling) {
        // Node 1 is an element
        if (node.nodeType == 1) {
            next = WickedLinkValidator._lookForwardByIdHelper(node, id);
            if (next != null) {
                return next;
            }
        }
    }
    if (elt.parentNode) {
        return WickedLinkValidator.lookForwardById(elt.parentNode, id, true);
    }
};

WickedLinkValidator._lookForwardByIdHelper = function(elt, id) {
    if (elt['id'] == id) {
        return elt;
    }
    for (var node = elt.childNodes[0]; node != null; node = node.nextSibling) {
        var found = WickedLinkValidator.lookForwardById(node, id);
        if (found != null) {
            return found;
        }
    }
}

